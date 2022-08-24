import sys
from urllib.parse import urlencode, parse_qsl
import xbmcgui
import xbmcplugin
import requests
from bs4 import BeautifulSoup
import re

URL = sys.argv[0]
HANDLE = int(sys.argv[1])

ACTION_VIDEOS = 'videos'
ACTION_SOURCES = 'sources'
ACTION_PLAY = 'play'

BASE_URL = 'https://www.66s.cc'
HEADERS = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_0_2 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12A366 Safari/600.1.4'}
LINKS = [
    {'name':'首页','path':'/'},
    {'name':'喜剧片','path':'/xijupian/'},
    {'name':'动作片','path':'/dongzuopian/'},
    {'name':'爱情片','path':'/aiqingpian/'},
    {'name':'科幻片','path':'/kehuanpian/'},
    {'name':'恐怖片','path':'/kongbupian/'},
    {'name':'剧情片','path':'/juqingpian/'},
    {'name':'战争片','path':'/zhanzhengpian/'},
    {'name':'纪录片','path':'/jilupian/'},
    {'name':'动画片','path':'/donghuapian/'},
    {'name':'电视剧','path':'/dianshiju/'},
    {'name':'综艺','path':'/ZongYi/'},
]


def get_url(**kwargs):
    """将参数转成路由地址"""
    return '{}?{}'.format(URL, urlencode(kwargs))


def get_response(path):
    """获取HTML响应内容"""
    resp = requests.get(BASE_URL + path)
    resp.encoding = 'utf-8'
    return resp.text


def get_soup(path):
    """获取HTML解析器"""
    return BeautifulSoup(get_response(path), "html.parser")


def get_prev_page_path(soup):
    """获取上一页地址"""
    node = soup.find('div', class_='pagination').find('a', class_='prev', text='上一页')
    if node is None:
        return None
    return node.get('href')


def get_next_page_path(soup):
    """获取下一页地址"""
    node = soup.find('div', class_='pagination').find('a', class_='next', text='下一页')
    if node is None:
        return None
    return node.get('href')


def get_videos(soup):
    """获取视频列表"""
    videos = []
    elements=soup.select("li.post.box.row.fixed-hight")

    if elements is not None:
        for element in elements:
            video = {}
            video['name'] = element.find('a', class_='zoom')['title']
            video['path'] = element.find('a', class_='zoom')['href']
            video['genre'] = element.find('span', class_='info_category').find('a').text
            thumb = element.find('img')
            if thumb:
                video['thumb'] = thumb['src']
            else:
                video['thumb'] = None
            videos.append(video)
    return videos


def get_sources(soup):
    """获取播放源列表"""
    sources = []
    source_title = soup.find('div', class_='context').find('h3', text='播放地址（无需安装插件）')
    if source_title is not None:
        source_element = source_title.parent
        source_items = source_element.find_all('a')
        for item in source_items:
            source = {}
            source['name'] = item['title']
            source['path'] = item['href']
            sources.append(source)
    return sources


def get_stream_url(path):
    """获取视频流URL"""
    resp = get_response(path)
    it = re.finditer(r"a:\'(.*)\'", resp)
    try:
        return next(it).group(1)
    except StopIteration:
        return None


def list_categories():
    xbmcplugin.setPluginCategory(HANDLE, '新版6v电影')
    xbmcplugin.setContent(HANDLE, 'videos')
    for link in LINKS:
        name = link['name']
        list_item = xbmcgui.ListItem(label=name)
        url = get_url(action=ACTION_VIDEOS, category=name, path=link['path'])
        is_folder = True
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_videos(category, path):
    xbmcplugin.setPluginCategory(HANDLE, category)
    xbmcplugin.setContent(HANDLE, 'videos')
    soup = get_soup(path)
    # 添加上一页
    prev = get_prev_page_path(soup)
    if prev:
        prev_list_item = xbmcgui.ListItem(label='上一页')
        prev_url = get_url(action=ACTION_VIDEOS, category=category, path=prev)
        xbmcplugin.addDirectoryItem(HANDLE, prev_url, prev_list_item, True)
    # 添加下一页
    next = get_next_page_path(soup)
    if next:
        next_list_item = xbmcgui.ListItem(label='下一页')
        next_url = get_url(action=ACTION_VIDEOS, category=category, path=next)
        xbmcplugin.addDirectoryItem(HANDLE, next_url, next_list_item, True)
    # 添加视频列表
    videos = get_videos(soup)
    for video in videos:
        video_name = video['name']
        thumb = video['thumb']
        list_item = xbmcgui.ListItem(label=video_name)
        list_item.setInfo('video', {'title': video_name,
                                    'genre': video['genre'],
                                    'mediatype': 'video'})
        if thumb:
            list_item.setArt({'thumb': thumb, 'icon': thumb, 'fanart': thumb})
        url = get_url(action=ACTION_SOURCES, category=video['name'], path=video['path'])
        is_folder = True
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def list_sources(category, path):
    xbmcplugin.setPluginCategory(HANDLE, category)
    xbmcplugin.setContent(HANDLE, 'videos')
    sources = get_sources(get_soup(path))
    for source in sources:
        list_item = xbmcgui.ListItem(label=source['name'])
        list_item.setInfo('video', {'title': source['name'],
                                    'mediatype': 'video'})
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action=ACTION_PLAY, path=source['path'])
        is_folder = False
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(HANDLE)


def play_video(path):
    stream_url = get_stream_url(path)
    if stream_url:
        xbmcplugin.setResolvedUrl(HANDLE, True, xbmcgui.ListItem(path=stream_url))
    else:
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    print(params)
    if params:
        if params['action'] == ACTION_VIDEOS:
            list_videos(category=params['category'], path=params['path'])
        elif params['action'] == ACTION_SOURCES:
            list_sources(category=params['category'], path=params['path'])
        elif params['action'] == ACTION_PLAY:
            play_video(params['path'])
        else:
            raise ValueError('Invalid paramstring: {}!'.format(paramstring))
    else:
        list_categories()


if __name__ == '__main__':
    router(sys.argv[2][1:])
