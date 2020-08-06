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

### root.py
This script parses a list of sites. 
```
python root.py SITES.txt
```
Where ```SITES.txt``` is a ```.txt``` file with line separated URL's

This script will start ```N``` threads where ```N``` is the number of sites in ```SITES.txt```

#### level1.py & level2.py
These scripts will parse lists of sites collected in the database according to the site base URL

If in mongodb collection ```root``` there exists an entry for ```example.com``` with a list of URL's, then those URL's will be parsed IF ```example.com``` is inside ```SITES.txt```

```
python level1.py SITES.txt NUM_CORES
or
python level2.py SITES.txt NUM_CORES
```
Where ```SITES.txt``` is a ```.txt``` file with line separated URL's
Where ```NUM_CORES``` is the number of cores used. If your computer has 4 cores, then put at most 4. Using the maximum number of cores may not give optimal performance.

NOTE: My Lenovo Thinkpad T450 Quad-Core had problems running with 4 cores!
On my computer, optimal performance is 2/3 cores (3 being a bit faster)