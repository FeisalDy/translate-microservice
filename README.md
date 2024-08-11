<p align="center">
  <img src="https://github.com/vTuanpham/Large_dataset_translator/assets/82665400/e424f17d-1c9e-4c72-90d2-9ef77c3b9dd2" width="100" height="100">
</p>

<div align="center">
  <h1>Large Dataset Translator</h1>
</div>

<p align="center">
  <a href="https://colab.research.google.com/drive/1OEni8c9N9C_9Kf3ySt87goN7HDvRN3nw?usp=sharing">
    <img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab">
  </a>
</p>

The Large Dataset Translator is a powerful solution designed to efficiently translate large datasets into various languages. It offers a streamlined and parallelized translation process, ensuring fast results without the need for an API key. The tool supports multithreaded processing, enabling users to translate extensive datasets in less time. It also includes an automatic fail-restart mechanism, ensuring uninterrupted translation in case of any issues.

### Key Features

- **Parallelized Translation**: Utilizes multithreaded processing to divide large datasets into chunks and translate them in parallel, significantly reducing processing time.
  
- **Handling Large Lists**: Efficiently handles datasets with large lists (e.g., dialogs) by splitting them into sub-lists and translating each sub-list in parallel.

- **Automatic Retry Mechanism**: Automatically restarts any failed translation threads, ensuring all data points are fully translated.

- **Data Format Compatibility**: Converts datasets into formats supported by pyarrow and huggingface-datasets for seamless integration.

- **Pre-Translation Filters**: Apply filters before translation, such as removing examples that may contain code.

- **GIL Resilience**: Python Global Interpreter Lock (GIL) does not impact speed, as tasks primarily involve I/O-bound operations.

- **Automatic Download**: Automatically downloads the converted dataset and translated dataset on Colab upon completion.

- **Unlimited Translation**: No API key required, making it ideal for translating large datasets without limitations.

### Demonstration

Here's a demo of the DataParser class, translating 1507 rows of text to Korean in under 2 minutes:

![Translation demo](assets/Translate_demo_vs.gif)

The translation split logic:
![Translation split logic](assets/Translation_pipe.drawio.pdf.png)


### Setup

#### Local Machine
```sh
git clone https://github.com/vTuanpham/Large_dataset_translator.git
     
cd Large_dataset_translator
  
# Set up virtual environment
virtualenv trans-env
  
# Activate virtual environment
source trans-env/bin/activate
  
bash install.sh

```
##### Google Colab
```sh
!git clone https://github.com/vTuanpham/Large_dataset_translator.git
 
%cd Large_dataset_translator

!bash install.sh
```
### Testing
Run the provided test script to ensure the tool works correctly. This should take about 10-20 minutes on a local machine or 5-10 minutes on Colab.
##### Local Machine:
```sh
python examples/YahmaAlpaca/AlpacaCleaned_Parser.py
```
##### Colab [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1OEni8c9N9C_9Kf3ySt87goN7HDvRN3nw?usp=sharing)
```sh
%run examples/YahmaAlpaca/AlpacaCleaned_Parser.py
```
Check the examples/YahmaAlpaca directory when the script finished, there should be a parsed dataset and a vietnamese dataset. 

#### LLM-based Translation
For a higher quality translation using LLM with context-aware translation, you can utilize the following script:

```sh
%run examples/argilla-magpie-ultra-v0.1-groq/MagpieUltraV01.py
```
or locally with:
```sh
python examples/argilla-magpie-ultra-v0.1-groq/MagpieUltraV01.py
```

This script is capable of translating approximately 100 examples every 6-7 minutes using Groq. To use it, you will need to obtain a free [API key](https://console.groq.com/keys) and set the environment variable by executing `export GROQ_API_KEY=<your_api_key>`.


## Usage
### To translate your own dataset:
1.  Inherit the DataParser class and implement your read and convert logic.
2.  Ensure the convert function maps all fields from the original dataset to those in configs/base_config.py, or choose other configs that fit your dataset.
3.  Set do_translate=True in the super call to enable translation.
   
    ```python
      def __init__(self, file_path: str, output_path: str):
        super().__init__(file_path, output_path,
                         parser_name=PARSER_NAME,
                         do_translate=True,
                         no_translated_code=True,
                         target_lang="ko")
    ```
5.  Customize translation settings such as target language and pre-translation filters.
### Pull requests are welcome for new dataset conversion examples 😎
## Supported Languages
The tool supports translation into a wide array of languages. Refer to the table in google's documentation for the complete list.
https://cloud.google.com/translate/docs/languages
## Known Issues
  * 'TypeError: "NoneType' object is not iterable"
     This issue is relevant to gender-specific translation, you can read more here https://github.com/ssut/py-googletrans/issues/260
#### Feel free to star 🌟 the repository if the test was successful!
#### Disclaimer: This repo is for private use only.




