import json
import sys
import urllib.parse
import xbmc
import xbmcgui


def rpc(method, params):
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    })
    raw = xbmc.executeJSONRPC(payload)
    try:
        return json.loads(raw).get("result", {})
    except Exception:
        return {}


def parse_args(argv):
    args = {}
    for item in argv[1:]:
        if "=" in item:
            k, v = item.split("=", 1)
            args[k.strip()] = urllib.parse.unquote(v.strip())
    return args


def find_movie(dbid_str, title, year_str):
    props = ["title", "year", "file", "art", "setid", "imdbnumber"]
    if dbid_str.isdigit():
        res = rpc("VideoLibrary.GetMovieDetails", {
            "movieid": int(dbid_str),
            "properties": props,
        })
        details = res.get("moviedetails")
        if details and details.get("label"):
            return details

    if title:
        res = rpc("VideoLibrary.GetMovies", {"properties": props})
        movies = res.get("movies") or []
        title_l = title.strip().lower()
        year_int = int(year_str) if year_str.isdigit() else None

        for m in movies:
            if (m.get("title") or "").strip().lower() == title_l:
                if year_int is None or m.get("year") == year_int:
                    return m
        for m in movies:
            if (m.get("title") or "").strip().lower() == title_l:
                return m
    return None


def find_tvshow(dbid_str, title, year_str):
    props = ["title", "year", "file", "art", "imdbnumber"]
    if dbid_str.isdigit():
        res = rpc("VideoLibrary.GetTVShowDetails", {
            "tvshowid": int(dbid_str),
            "properties": props,
        })
        details = res.get("tvshowdetails")
        if details and details.get("label"):
            return details

    if title:
        res = rpc("VideoLibrary.GetTVShows", {"properties": props})
        shows = res.get("tvshows") or []
        title_l = title.strip().lower()
        for s in shows:
            if (s.get("title") or "").strip().lower() == title_l:
                return s
    return None


def main():
    args = parse_args(sys.argv)
    dbtype = (args.get("dbtype") or "movie").lower()
    dbid = args.get("dbid") or ""
    title = args.get("title") or ""
    year = args.get("year") or ""
    folderpath = args.get("folderpath") or ""

    home = xbmcgui.Window(10000)
    home.clearProperty("AdditionalInfo")
    home.clearProperty("CloseInfoDialog")

    xbmc.executebuiltin("Dialog.Close(MovieInformation,true)")
    xbmc.sleep(120)

    item = find_tvshow(dbid, title, year) if dbtype == "tvshow" else find_movie(dbid, title, year)
    if not item:
        if "?" in folderpath:
            home.setProperty("SetCustomAddon", "1")
            xbmc.executebuiltin(
                f"RunScript(plugin.video.tmdb.bingie.helper,add_path={urllib.parse.quote(folderpath)},call_auto=1190)"
            )
        else:
            xbmcgui.Dialog().notification("Local Info", f"Not found in library: {title}", xbmcgui.NOTIFICATION_WARNING, 3000)
        return

    home.clearProperty("SetCustomAddon")

    li = xbmcgui.ListItem(label=item.get("title") or item.get("label") or title)
    info_tag = li.getVideoInfoTag()
    if item.get("title"):
        info_tag.setTitle(item["title"])
    if item.get("year"):
        info_tag.setYear(int(item["year"]))
    if item.get("imdbnumber"):
        info_tag.setIMDBNumber(str(item["imdbnumber"]))
    if item.get("file"):
        li.setPath(item["file"])

    art = dict(item.get("art") or {})
    if "clearlogo" not in art and "logo" in art:
        art["clearlogo"] = art["logo"]
    if art:
        li.setArt(art)

    if dbtype == "tvshow" and item.get("tvshowid"):
        li.setProperty("dbid", str(item["tvshowid"]))
        info_tag.setDbId(int(item["tvshowid"]))
    elif item.get("movieid"):
        li.setProperty("dbid", str(item["movieid"]))
        info_tag.setDbId(int(item["movieid"]))

    xbmcgui.Dialog().info(li)


if __name__ == "__main__":
    main()
