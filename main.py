import requests
import json
from discord.ext import commands
import discord
from webserver import keep_alive
from dateutil import parser
import pytz
from os import system
import time

bot = commands.Bot(command_prefix="!", help_command=None)

headers = {
    "user-agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
}


def api_link(styleColor, merchGroup, country):
    mx_api = f"https://api.nike.com/deliver/available_gtins/v2/?filter=styleColor%28{styleColor}%29&filter=shipNode%28MX_FAST%29"
    api = f"https://api.nike.com/deliver/available_gtins/v2/?filter=styleColor%28{styleColor}%29&filter=merchGroup%28{merchGroup}%29"
    if country == "MX" or country == "mx":
        return mx_api
    else:
        return api


def link(styleColor, countryCode, language, mode):
    webstoreURL = f"https://api.nike.com/product_feed/threads/v2/?filter=marketplace%28{countryCode}%29&filter=language%28{language}%29&filter=channelId%28d9a5bc42-4b9c-4976-858a-f159cf99c647%29&filter=productInfo.merchProduct.styleColor%28{styleColor}%29"
    snkrsURL = f"https://api.nike.com/product_feed/threads/v2/?filter=marketplace%28{countryCode}%29&filter=language%28{language}%29&filter=channelId%28010794e5-35fe-4e32-aaff-cd2c74f89d61%29&filter=productInfo.merchProduct.styleColor%28{styleColor}%29"
    if mode == "webstore":
        return webstoreURL
    else:
        return snkrsURL


@bot.command()
async def run(country, styleColor, mode, ctx):
    storage = []
    api_level = []
    backend_level = []

    upcomingItem = {}
    dates = {}
    sizes = []
    f = open("country_available.json")
    data = json.load(f)

    country = country.lower()
    for item in data["region"]:
        if country == item["country"]:
            countryCode = item["country"]
            country = countryCode.upper()
            language = item["language"]
            merchGroup = item["merchGroup"]
            storage.append(country)
            storage.append(language)
            storage.append(merchGroup)

    mx_api = f"https://api.nike.com/deliver/available_gtins/v2/?filter=styleColor%28{styleColor}%29&filter=shipNode%28MX_FAST%29"
    api = f"https://api.nike.com/deliver/available_gtins/v2/?filter=styleColor%28{styleColor}%29&filter=merchGroup%28{storage[2]}%29"

    if country == "MX" or country == "mx":
        requests2 = requests.get(mx_api, headers=headers).json()
    else:
        requests2 = requests.get(api, headers=headers).json()

    for stockLevel in requests2["objects"]:
        level = {}
        level["gtin"] = stockLevel["gtin"]
        level["level"] = stockLevel["level"]
        api_level.append(level)

    snkrsURL = f"https://api.nike.com/product_feed/threads/v2/?filter=marketplace%28{storage[0]}%29&filter=language%28{storage[1]}%29&filter=channelId%28010794e5-35fe-4e32-aaff-cd2c74f89d61%29&filter=productInfo.merchProduct.styleColor%28{styleColor}%29"
    stockx = "https://stockx.com/search?s=" + styleColor
    goat = "https://www.goat.com/search?query=" + styleColor

    request = requests.get(snkrsURL, headers=headers).json()
    checking = []
    pages = request["pages"]["totalPages"]
    checking.append(pages)
    if checking[0] == 0:
        embed = discord.Embed(title="Item not found!", color=0x00ff00)
        await ctx.send(embed=embed)
    else:
        for product in request["objects"]:
            for item in product["productInfo"]:
                if item['merchProduct']['styleColor'] == styleColor:
                    if mode == 'snkrs':
                        upcomingItem["shoeTitle"] = \
                        product["publishedContent"]["properties"]["coverCard"]["properties"]["subtitle"]
                        upcomingItem["shoeNickname"] = \
                        product["publishedContent"]["properties"]["coverCard"]["properties"]["title"]
                        upcomingItem["productUrl"] = f"https://www.nike.com/{storage[0].lower()}/launch/t/" + \
                                                     product["publishedContent"]["properties"]["seo"]["slug"]
                        try:
                            item["launchView"]
                        except KeyError:
                            item
                        else:
                            upcomingItem["launchMethod"] = item["launchView"]["method"]
                            upcomingItem["launchStart"] = item["launchView"]["startEntryDate"]
                            try:
                                upcomingItem["launchEnd"] = item["launchView"]["stopEntryDate"]
                            except KeyError:
                                upcomingItem["launchEnd"] = "Not Found"
                    elif mode == 'nike':
                        upcomingItem["shoeTitle"] = product["publishedContent"]["properties"]["title"]
                        upcomingItem["shoeNickname"] = product["publishedContent"]["properties"]["subtitle"]
                        upcomingItem["productUrl"] = f"https://www.nike.com/{storage[0].lower()}/t/" + \
                                                     product["publishedContent"]["properties"]["seo"][
                                                         "slug"] + f"/{styleColor}"
                        try:
                            upcomingItem["startDate"] = item["launchView"]["startEntryDate"]
                        except KeyError:
                            upcomingItem["startDate"] = item["merchProduct"]["commerceStartDate"]
                        try:
                            upcomingItem["publishType"] = item["launchView"]["method"]
                        except KeyError:
                            try:
                                upcomingItem["publishType"] = item["merchProduct"]["publishType"]
                            except KeyError:
                                upcomingItem["publishType"] = "UNDEFINED"
                    upcomingItem["currency"] = item["merchPrice"]["currency"]
                    upcomingItem["price"] = item["merchPrice"]["fullPrice"]
                    upcomingItem["colorway"] = item["productContent"]["colorDescription"]
                    upcomingItem["quantityLimit"] = item["merchProduct"]["quantityLimit"]
                    upcomingItem["marketplace"] = product["marketplace"]
                    upcomingItem["status"] = item["merchProduct"]["status"]
                    upcomingItem["imgUrl"] = item["imageUrls"]["productImageUrl"]
                    try:
                        item["skus"]
                    except KeyError:
                        item
                    else:
                        for shoeSize in item["skus"]:
                            for cm in shoeSize["countrySpecifications"]:
                                tempSize = {}
                                tempSize["gtin"] = shoeSize["gtin"]
                                if country == "MX":
                                    tempSize["nikeSize"] = shoeSize["nikeSize"] + " / " + cm["localizedSize"] + "CM"
                                else:
                                    tempSize["nikeSize"] = shoeSize["nikeSize"]
                                backend_level.append(tempSize)
        for item1 in api_level:
            for item2 in backend_level:
                listing = {}
                asdf = []
                if item1["gtin"] == item2["gtin"]:
                    listing["nikeSize"] = item2["nikeSize"]
                    listing["level"] = item1["level"]
                    size = listing["nikeSize"]
                    level = listing["level"]
                    asdf.append("US")
                    asdf.append(size)
                    asdf.append("--**" + level + "**\n")
                    sizes.append(asdf)
        itemName = upcomingItem["shoeTitle"] + " " + upcomingItem["shoeNickname"]
        pricing = upcomingItem["currency"] + " " + str(upcomingItem["price"])
        latest = []
        try:
            sizes.sort(key=lambda company: float(company[1]))
            for item in sizes:
                xxxx = ' '.join(c for c in (item))
                latest.append(xxxx)
        except ValueError:
            for item in sizes:
                xxxx = ' '.join(c for c in (item))
                latest.append(xxxx)
        usethis = ' '.join(a for a in latest)
        timezone = pytz.timezone('Asia/Kuala_Lumpur')
        if mode == 'snkrs':
            try:
                date = parser.parse(upcomingItem["launchStart"]).astimezone(tz=timezone)
                dates['date1'] = (date.strftime('%Y-%m-%d %I:%M:%S%p'))
            except:
                dates['date1'] = "Not Found"
            try:
                date = parser.parse(upcomingItem["launchEnd"]).astimezone(tz=timezone)
                dates['date2'] = (date.strftime('%Y-%m-%d %I:%M:%S%p'))
            except:
                dates['date2'] = "Not Found"
                pass
        elif mode == 'nike':
            date = parser.parse(upcomingItem['startDate']).astimezone(tz=timezone)
            dates['date1'] = (date.strftime('%Y-%m-%d %I:%M:%S%p'))

        links = f"[StockX]({stockx})"
        links2 = f"[Goat]({goat})"
        embed = discord.Embed(title=itemName, url=upcomingItem['productUrl'], color=0x00ff00)
        embed.set_thumbnail(url=upcomingItem["imgUrl"])
        embed.add_field(name="Status", value=upcomingItem["status"])
        if mode == 'snkrs':
            embed.add_field(name="Launch Method", value=upcomingItem["launchMethod"])
        elif mode == 'nike':
            embed.add_field(name="Method", value=upcomingItem["publishType"], inline=True)
        embed.add_field(name="Cart Limit", value=upcomingItem["quantityLimit"], inline=True)
        embed.add_field(name="Style Color", value=styleColor, inline=True)
        embed.add_field(name="Country", value=upcomingItem["marketplace"], inline=True)
        embed.add_field(name="Price", value=pricing, inline=True)
        embed.add_field(name="Colorway", value=upcomingItem["colorway"], inline=True)
        if mode == 'snkrs':
            embed.add_field(name="LaunchStart", value=dates['date1'], inline=False)
            embed.add_field(name="LaunchEnd", value=dates['date2'], inline=False)
        elif mode == 'nike':
            embed.add_field(name="Start Date", value=dates['date1'], inline=False)
        if usethis is not None:
            embed.add_field(name="Size Available", value=usethis)
        else:
            embed.add_field(name="Size Available", value="No Size Yet")
        embed.add_field(name="Links", value=links + " | " + links2, inline=False)
        await ctx.send(embed=embed)
        print(upcomingItem)


@bot.command(pass_context=True)
async def snkrs(ctx, styleColor, country):
    mode = 'snkrs'
    await run(country, styleColor, mode, ctx)


@bot.command(pass_context=True)
async def nike(ctx, styleColor, country):
    mode = 'nike'
    await run(country, styleColor, mode, ctx)


@bot.command()
async def launch(ctx, country):
    results = []
    with open("country_available.json") as f:
        jdata = json.load(f)
    countryList = []
    for item in jdata['region']:
        temp = {}
        temp['country'] = item['country'].upper()
        temp['language'] = item['language']
        countryList.append(temp)

    newCountry = country.upper()

    tempLanguage = []
    for item in countryList:
        item['country'].upper()
        if item['country'] == newCountry:
            tempLanguage.append(item['language'])
    url = f"https://api.nike.com/product_feed/threads/v2/?filter=marketplace%28{newCountry}%29&filter=language%28{tempLanguage[0]}%29&filter=employeePrice%28true%29&filter=upcoming%28true%29&filter=channelId%28010794e5-35fe-4e32-aaff-cd2c74f89d61%29&sort=effectiveStartSellDateAsc&fields=active,id,lastFetchTime,productInfo,publishedContent.nodes,publishedContent.subType,publishedContent.properties.coverCard,publishedContent.properties.productCard,publishedContent.properties.products,publishedContent.properties.publish.collections,publishedContent.properties.relatedThreads,publishedContent.properties.seo,publishedContent.properties.threadType,publishedContent.properties.custom,publishedContent.properties.title"
    print(url)
    timezone = pytz.timezone('Asia/Kuala_Lumpur')
    launches = requests.get(url, headers=headers)
    for product in launches.json()["objects"]:
        for item in product["productInfo"]:
            upcomingItem = {}
            upcomingItem["shoeTitle"] = product["publishedContent"]["properties"]["coverCard"]["properties"]["subtitle"]
            upcomingItem["shoeNickname"] = product["publishedContent"]["properties"]["coverCard"]["properties"]["title"]
            upcomingItem["gender"] = item["merchProduct"]["genders"]
            upcomingItem["price"] = str(item["merchPrice"]["currency"] + " " + str(item["merchPrice"]["fullPrice"]))
            upcomingItem["productUrl"] = f"https://www.nike.com/{newCountry.lower()}/launch/t/" + \
                                         product["publishedContent"]["properties"]["seo"]["slug"]
            upcomingItem["colorway"] = item["productContent"]["colorDescription"]
            upcomingItem["styleColor"] = item["merchProduct"]["styleColor"]
            upcomingItem["quantityLimit"] = item["merchProduct"]["quantityLimit"]
            try:
                item["launchView"]
            except KeyError:
                item
            else:
                try:
                    upcomingItem["launchMethod"] = item["launchView"]["method"]
                except KeyError:
                    upcomingItem["launchMethod"] = "Not Found"
                try:
                    date = parser.parse(item["launchView"]["startEntryDate"]).astimezone(tz=timezone)
                    date1 = (date.strftime('%Y-%m-%d %I:%M:%S%p'))
                    upcomingItem["launchStart"] = date1
                except KeyError:
                    upcomingItem["launchStart"] = "Not Found"
                try:
                    date = parser.parse(item["launchView"]["stopEntryDate"]).astimezone(tz=timezone)
                    date2 = (date.strftime('%Y-%m-%d %I:%M:%S%p'))
                    upcomingItem["launchEnd"] = date2
                except KeyError:
                    upcomingItem["launchEnd"] = "Not Found"
            upcomingItem["imgUrl"] = item["imageUrls"]["productImageUrl"]
            results.append(upcomingItem)
    for item in results:
        stockx = "https://stockx.com/search?s=" + item['styleColor']
        goat = "https://www.goat.com/search?query=" + item['styleColor']
        links = f"[StockX]({stockx})"
        links2 = f"[Goat]({goat})"
        try:
            embed = discord.Embed(title=item['shoeTitle'] + " " + item['shoeNickname'], url=item['productUrl'],
                                  color=0x00ff00)
            embed.set_thumbnail(url=item["imgUrl"])
            embed.add_field(name="Launch Method", value=item["launchMethod"])
            embed.add_field(name="Cart Limit", value=item["quantityLimit"])
            embed.add_field(name="Style Color", value=item["styleColor"])
            embed.add_field(name="Price", value=item["price"], inline=False)
            embed.add_field(name="Colorway", value=item["colorway"], inline=False)
            embed.add_field(name="LaunchStart", value=item['launchStart'], inline=False)
            embed.add_field(name="LaunchEnd", value=item['launchEnd'], inline=False)
            embed.add_field(name="Links", value=links + " | " + links2, inline=False)
            await ctx.send(embed=embed)
        except KeyError:
            print(item)
        time.sleep(1)


keep_alive()
token = 'YOUR DISCORD TOKEN'


def play():
    try:
        bot.run(token)
    # except discord.errors.HTTPException:
    except:
        system("python restarter.py")
        system('kill 1')


while True:
    play()
    time.sleep(1800)
    print("Done")
