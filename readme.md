### Quick Start

First, please install all the requirements, and run the following code in the terminal:

```python
pip install flask folium googlemaps
```

You can also install these packages in the PyCharm settings.

Note that Google Maps is **OPTIONAL**, because our json data is ready, you don't need to run the `generate_graph_json.py` again.

To protect privacy, we delete our Google map API key in `generate_graph_json.py`, so this program cannot run without the API key.  If you want to test the method, you can apply the key at [Google Maps Platform ](https://developers.google.com/maps). Our program will not call the API key to many times, even not over the free trial limit.

Please **ensure** that there is a folder called `templates` in the working environment. It will store our temporary HTML file for the website



### Launch Guide

To begin, you can just run `main.py` in PyCharm or in the terminal(recommended):

```textile
cd #The file path that stores our project#
python main.py
```

Then visit `http://127.0.0.1:5000/` in your browser. The map of UofT and the marker with the buildings should be displayed.

> We've tested it on all platforms, so if you follow our guidelines, it's sure to run 😀



### Using guide

The main function of our program is to find the quickest path that can go through all the places that you choose.

Move the mouse to the places that you want to go, then click `select` bottom, the name of the place will be displayed at the top of the website.

After you choose the places, click the `Calculate` button, the program will calculate the quickest path and the time it will take, then display them on the website.

To calculate a new path, click `clear` bottom first, then follow the above guide again.



### Finally

We hope you have fun with our program and that it helps you.



> We would like to thank our Professor Sadia and the TAs for their guidance and help with this program; without them, there is no way we could have successfully completed this program.😊


