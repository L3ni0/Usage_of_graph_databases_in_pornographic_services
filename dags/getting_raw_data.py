# from pornhub_api import PornhubApi
# import json
# api = PornhbApi()
# all_stars =  {starobj.star.star_name: {
#                 "url": starobj.star.star_url,
#                 "gender": starobj.star.gender,
#                 "videos_count": starobj.star.videos_count_all
#     } for starobj in api.stars.all_detailed().stars
# }
# ll_stars = {}

# TODO:


import pornhub

client = pornhub.PornHub()
for star in client.getStars(11, sort_by="rank"):
    # print(star)
    print(star["name"])

    for i in client.getStarsVideos(star["name"], type=star["type"]):
        print(i)
        # print(client.getVideo(url=i))
