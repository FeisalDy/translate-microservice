@echo off
echo Installing dependencies...

pip install -r requirements.txt
pip install groq==0.9.0
pip install cerebras_cloud_sdk==1.5.0

IF "%GROQ_API_KEY%"=="" (
    echo GROQ_API_KEY environment variable is not set. Please set it to your project's GROQ API key to use the groq provider.
)

IF "%CEREBRAS_API_KEY%"=="" (
    echo CEREBRAS_API_KEY environment variable is not set. Please set it to your project's CEREBRAS API key to use the CEREBRAS provider.
)

pip install httpx==1.0.0.beta0 --force-reinstall
python string_ops\build.py

echo Installation completed successfully!
