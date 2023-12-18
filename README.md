## Usage

> Note: Download GDAL and Fiona for your Python version [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/) first.

Install the SRM requirements through the requirements file.

```
$ pip install -r requirements.txt
```

Run the flask app. (development)

```
$ flask run
```

Run the flask app. (production, windows)
```
$ waitress-serve wsgi:app
```
hosted on localhost:8080