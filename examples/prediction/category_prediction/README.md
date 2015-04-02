# Word Prediction / classification example:

### Run with ` ./run.py`

This will read the specified part of the provided textfile, tokenize the words and remove stopwords.

Then, a HTM model using the CategoryEncoder and fitting parameters is built and used to classify the read words.

The model predicts the next word for each word in a story, treating each word as a predefined category.

After running the model, `tokens.txt` will contain all the relevant word tokens and `results.csv` will list the predicted probabilities for each.

### Clean directory with `./clean.py`

Use this simply to reset the generated files. Strongly recommended if you intend to use this code multiple times!

### Adapt this example for your needs

Feel free to modify and change the code to meet the needs for your classification-problem.
You might for example change the stopwords in `stopwords.txt`, edit the MODEL_PARAMS or simply choose a different story/text to classify. 
For JACK AND THE BEANSTALK use indices 129017 - 138889.
