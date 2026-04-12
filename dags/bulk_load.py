import pornhub
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from neo4j import GraphDatabase
from datetime import datetime
import traceback


class DataLoader:
    def __init__(self) -> None:
        # conf
        self.POSTGRES_URL = "postgresql+psycopg2://user:password@localhost:5432/star_db"
        self.NEO4J_URI = "neo4j://localhost:7687"
        self.NEO4J_AUTH = ("neo4j", "airflowpassword")

        self.client = pornhub.PornHub()

        self.star_cache = {}
        self.category_cache = {}
        self.tag_cache = {}

    def _clean_list(self, items: list | tuple):
        """Drop empty strings and None's."""
        if not items:
            return []
        return [item.strip() for item in items if item and item.strip()]

    def _string_to_int(self, string_numb: str) -> int:
        int_numb = int(string_numb.replace("K", "000").replace("M", "000000"))
        return int_numb

    def bulk_load_to_neo4j(self, videos_data):
        driver = GraphDatabase.driver(self.NEO4J_URI, auth=self.NEO4J_AUTH)

        bulk_query = """
        UNWIND $videos AS video
        MERGE (v:Video {url: video.url})
        SET v += video.properties

        WITH v, video
        FOREACH (star_name IN video.pstars |
            MERGE (s:Star {name: star_name})
            MERGE (s)-[:APPEARS_IN]->(v)
        )

        WITH v, video
        FOREACH (category_name IN video.categories |
            MERGE (c:Category {name: category_name})
            MERGE (v)-[:IN_CATEGORY]->(c)
        )

        WITH v, video
        FOREACH (tag_name IN video.tags |
            MERGE (t:Tag {name: tag_name})
            MERGE (v)-[:HAS_TAG]->(t)
        )
        """

        def normalise_views(video: dict) -> int:
            views = video.get("accurate_views")
            if views is None:
                views_str = video.get("views", "0")
                views = self._string_to_int(views_str)
            return views

        def normalise_likes(video: dict) -> int:
            likes = video.get("accurate_likes")
            if likes is None:
                likes = 0
            elif isinstance(likes, str):
                likes = self._string_to_int(likes)
            return likes

        try:
            with driver.session(database="neo4j") as session:
                neo4j_videos = []
                for video in videos_data:
                    pstars = self._clean_list(video.get("pornstars", []))
                    categories = self._clean_list(video.get("categories", []))
                    tags = self._clean_list(video.get("tags", []))

                    views = normalise_views(video)
                    likes = normalise_likes(video)

                    neo4j_videos.append(
                        {
                            "url": video.get("url"),
                            "properties": {
                                "title": video.get("title", ""),
                                "views": views,
                                "duration": video.get("duration", ""),
                                "author": video.get("author", ""),
                                "upload_date": video.get("upload_date", ""),
                                "likes": likes,
                                "rating": video.get("rating"),
                            },
                            "pstars": pstars,
                            "categories": categories,
                            "tags": tags,
                        },
                    )

                result = session.run(bulk_query, videos=neo4j_videos)
                summary = result.consume()
                print(
                    f"Neo4j:{summary.counters.nodes_created} edges loaded "
                    f"{summary.counters.relationships_created} relations"
                )

        except Exception as e:
            print(f"Neo4j: {e}")
            traceback.print_exc()
        finally:
            driver.close()

    def run_optimized(self, limit_stars: int | None = None) -> None:
        if limit_stars:
            stars_generator = self.client.getStars(quantity=limit_stars, sort_by="rank")
        else:
            stars_generator = self.client.getStars(infinity=True, sort_by="rank")

        for star_data in stars_generator:
            star_name = star_data["name"]
            print(f"\n {star_name}")
            all_videos_data = []

            try:
                video_urls = self.client.getStarsVideos(
                    star_name,
                    type=star_data.get("type"),
                )

                for video_url in set(video_urls):
                    try:
                        print(f"{video_url}")
                        video_details = self.client.getVideo(url=video_url)
                        if video_details and video_details.get("url"):
                            all_videos_data.append(video_details)
                    except Exception as e:
                        print(f"error: {video_url}: {e}")
                        continue

                print(f"{len(all_videos_data)} videos")

                if all_videos_data:
                    print("Loading to Neo4j")
                    self.bulk_load_to_neo4j(all_videos_data)

            except Exception as e:
                print(f"error for star:{star_name}: {e}")
                traceback.print_exc()
                continue


if __name__ == "__main__":
    loader = DataLoader()
    loader.run_optimized()
