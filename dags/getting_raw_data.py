import pornhub


client = pornhub.PornHub()
for star in client.getStars(11, sort_by="rank"):
    # print(star)
    print(star["name"])

    for i in client.getStarsVideos(star["name"], type=star["type"]):
        print(i)
        print(client.getVideo(url=i))
