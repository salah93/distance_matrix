# Distance Calculator
An app built for [crosscompute](https://crosscompute.com/docs)

use googles distance matrix api to find the location with least distance to all potential destinations

Must have google distance matrix api key saved as environment variable `GOOGLE_KEY`

I built this app to choose hotels when traveling to cities for conferences or weddings

## Requirements
+ python2
+ pip

## Steps
```
# update cc.ini accordingly
$ export GOOGLE_KEY="your-api-key"
$ pip install -r requirements.txt
$ crosscompute run
$ crosscompute serve
```
