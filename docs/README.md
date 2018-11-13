# Building the Documentation
* Ensure all requirements are met in the **requirements.txt** file.
* Using the command line/terminal, `cd` into **docs/**`.
* Perform `make clean`
* Perform `make html`
* With python3 installed, run `python -m http.server 5000` in the **docs/build/html/** directory.
* Go to `localhost:5000` to see the result.

Note: To see changes for the toctree without side effects, the documentss must be generated again. In this instance, one would do as follows:
* `ctrl + c` to stop the http server
* `make clean`
* `make html`
* `python -m http.server 5000` to start the server again
