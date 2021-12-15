#!/usr/bin/env python
import json
import math
import random
import urllib.error
import urllib.parse
import urllib.request
from flask import Flask, render_template, request
import logging

app = Flask(__name__)
api_key = '8ede641ca54482881b9f018a9e7b7779'


### Utility functions you may want to use
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)


# Takes a url returns stuff from url
def safe_get(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("The server couldn't fulfill the request.")
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We failed to reach a server")
        print("Reason: ", e.reason)
    return None


# Adds parameters to discover method, returns stuff from url
def getURL(baseurl='https://api.themoviedb.org/3/discover/movie',
           params={}):
    params['api_key'] = api_key
    filtered_params = {k: v for k, v in params.items() if v is not None}

    # print("params: "+params)
    url = baseurl + "?" + urllib.parse.urlencode(filtered_params)
    print("full url: " + url)
    return safe_get(url)

# Takes parameters and returns a movie id based on parameters
def discover(year=None, genre_id=None, runtime=None, language="en", page=1):
    print(language)
    result = getURL(params={"primary_release_year": year, "with_genres": genre_id, "with_runtime.lte": runtime,
                            "with_original_language": language})
    # print("result from discover: "+result)
    jsonresult = result.read()
    data = json.loads(jsonresult)  # all data from page 1
    print(pretty(data))
    if not data['results']:
        return 0
    else:
        movie_list = data['results']  # a list of dictionaries where each dictionary is a movie
        # random.shuffle(movie_list)
        # print(pretty(movie_list))
        rand_movie = random.choice(movie_list)  # choose a random movie
        # print("random movie id: " + str(rand_movie["id"]))
        return rand_movie["id"]

# Takes a movie id from discover and gets all the movie info.
# Returns a dictionary containing all data for that movie
def getMovie(id):
    baseurl = "https://api.themoviedb.org/3/movie/"
    url = baseurl + str(id) + "?" + "api_key=" + api_key
    # print("full url: " + url)
    result = safe_get(url)
    jsonresult = result.read()
    dict = json.loads(jsonresult)
    # print(pretty(dict))
    return dict

def getKeywords(id):
    baseurl = "https://api.themoviedb.org/3/movie/"
    url = baseurl + str(id) + "/" + "keywords?api_key=" + api_key
    # print("full url: " + url)
    result = safe_get(url)
    jsonresult = result.read()
    dict = json.loads(jsonresult)
    # print(pretty(dict))
    return dict


# Builds the poster path
def getImgURL(path):
    try:
        baseurl = "https://image.tmdb.org/t/p/w500"
        url = baseurl + path
        # print("full url: "+url)
        return url
    except:
        return "/static/placeholder.jpg"

def getRuntime(totalmin):
    if totalmin == 0:
        return "- hr - min"
    elif totalmin < 60:
        return "{} min".format(totalmin)
    hr = math.trunc(totalmin/60)
    min = str(totalmin%60)
    print("total minutes: "+str(totalmin)+" converted: "+"{} hr {} min".format(hr, min))
    return "{} hr {} min".format(hr, min)

# Takes a list of dictionaries [{id: 9, name: Action},{}]
# Returns a list of the genre names
def getGenre(genre_list):
    genre_names = [dict["name"] for dict in genre_list]
    return genre_names  # returns a list

def allGenres():
    result = getURL(baseurl="https://api.themoviedb.org/3/genre/movie/list")
    jsonresult = result.read()
    data = json.loads(jsonresult)  # list of dicts
    genre_dict = {}
    for dict in data['genres']:
        genre_dict[dict["id"]] = dict['name']
    return genre_dict

# returns a dict with all languages
def allLang():
    result = getURL(baseurl="https://api.themoviedb.org/3/configuration/languages")
    jsonresult = result.read()
    data = json.loads(jsonresult)  # list of dicts
    lang_dict = {}
    for dict in data:
        lang_dict[dict["iso_639_1"]] = dict['english_name']
    # print(pretty(lang_dict))
    return lang_dict

# searches in the lang dict returns the full name of the language for the abbr
def getLang(abbr):
    dict = allLang()
    return dict[abbr]


class Movie:
    def __init__(self, id):
        dictionary = getMovie(id)
        # print(pretty(dictionary))
        self.dictionary = dictionary
        self.title = dictionary['title']
        self.poster_path = getImgURL(dictionary['poster_path'])
        self.genres = getGenre(dictionary['genres'])  # returns a list of dicts
        self.overview = dictionary['overview']
        self.release_date = dictionary['release_date'][0:4]  # getting the year only
        self.movie_id = dictionary['id']
        self.runtime = getRuntime(dictionary['runtime'])
        self.language = getLang(dictionary['original_language'])
        self.watch_provider=getWatchProvider(self.movie_id)

    def __str__(self):
        s = '''Title: {self.title}\nRelease Year: {self.release_date}\nPoster Link: {self.poster_path}\nOverview: {self.overview}\nRuntime: {self.runtime}\nLanguage: {self.language}\nGenres: {self.genres}\nWatch Providers: {self.watch_provider}\nId: {self.movie_id}'''.format(
            self=self)
        return pretty(self.dictionary)

def getWatchProvider(id):
    result = safe_get("https://api.themoviedb.org/3/movie/" + str(id) + "/watch/providers?api_key=" + api_key)
    jsonresult = result.read()
    providers = json.loads(jsonresult)
    # print(pretty(providers["results"]))
    if "US" in providers["results"].keys():
        return providers["results"]["US"]["link"]
    else:
        return None

@app.route("/")
def main_handler():
    app.logger.info("In MainHandler")
    return render_template('form.html', languages=allLang(), genres=allGenres())


@app.route("/gresponse")
def greet_response_handler():
    # Get user parameters
    app.logger.info(request.args.get('year'))
    year = request.args.get('year')
    genre = request.args.get('genre')
    language = request.args.get('language')
    id = discover(year=year, genre_id=genre, language=language)
    print(id)
    if id == 0:
        print("here")
        return render_template('form.html', languages=allLang(), genres=allGenres(), prompt="No movies found. Please try another search.")
    else:
        chosen_movie = Movie(id)
        print(chosen_movie)
        if year or genre or language:
            # if form filled in, return a movie
            return render_template('result.html', movie=chosen_movie.title, year=chosen_movie.release_date,
                                   poster=chosen_movie.poster_path, overview=chosen_movie.overview,
                                   genre=chosen_movie.genres, language=chosen_movie.language, runtime=chosen_movie.runtime, provider=chosen_movie.watch_provider)
        else:
            # if not, then show the form again with a correction to the user
            return render_template('form.html', languages=allLang(), genres=allGenres(), prompt="Please enter a year or select a genre.")

@app.errorhandler(404)
def handle_bad_request(e):
    return 'No watch providers in the US!', 400

if __name__ == "__main__":
    # Used when running locally only.
    # When deploying to Google AppEngine, a webserver process will
    # serve your app.
    app.run(host="localhost", port=8080, debug=True)
