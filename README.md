# Scraper

## Setting up the environment

#### Virtualenv
I use virtualenv but it is not strictly speaking necessary

```
virtualenv venv
source /venv/bin/activate
```

#### Environment variables
You will need two environment variables, ```DATABASE``` and ```BROWSER```, for a database link and the address of the Selenium browser (optional)

```
export DATABASE=mongodb://root:example@192.168.1.35:27017/ <--- mine
export DATABASE=mongodb://user:password@address:port/
export BROWSERhttp://127.0.0.1:4444/wd/hub
```
#### Python packages installation
```
pip3 install -r requirements.txt
or
pip install -r requirements.txt
```

# Usage
```
python Parse.py example.com level duplicates 
```
Here ```level``` means the depth, default is ```0``` for ```root``` level.
Here ```duplicates``` means either save duplicates or not, indicated by ```0``` for not, ```1``` to save duplicates. Default is ```0```

#### Root crawling
For root page ```example.com``` the scraper will collect the HTML from the page and save it along with a list of all links that point to either ```subdomain.example.com``` or ```example.com/subdirectory```, in a mongodb collection called ```root```. 
There will also be created an entry for each link in the mongodb collection ```level_1```

```
python Parse.py example.com 0 0
```

#### Level crawling
To crawl all ```level_1``` URL's for ```example.com``` and not saving duplicate URL's, run

```
python Parse.py example.com 1 0
```

To save duplicate URL's, run

```
python Parse.py example.com 1 1
```

This will run in paralell with 10 threads crawling
