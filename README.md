# mycycle

I want to understand my menstrual cycle. I want to know when I ovulate and when my next period will be. 

In this repo, I share the tools I use to monitor my basal temperature and detect ovulation. 

## Set up python environment

This project uses python 3.12

I suggest to create a virtual environment. 

You can find the requirements in requirements.txt

## Files

`config.yaml` has important configuration parameters. 
`data/raw/temperatura.csv` is a csv file with some temperature data to play with (it is exported from a google sheet, using United States configuration)
`src` has the source code

## How to run the code and get the plots?

Execute
> python main.py

The results (a plot and a report) will be saved in the path_results defined in config.yaml 

## TODOs
This is work in progress. Be patient. 
1. Mejorar la estimación de la fecha de menstruación usando la fecha de ovulación (cuando esté disponible)
2. Hoy está la posibilidad de ingresar a mano una fecha de ovulacion con "probable_ovulaciones" pero el código no está claro
