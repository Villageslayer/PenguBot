# Step by Step Setup Guide PENGUBOT

1. Clone the Repo
```
git clone https://github.com/stormcoph/PenguBot
```

2. cd into it
```
cd PenguBot
```

3. Create venv 
```
py -3.11 -m venv .venv 
```
4. Activate venv
```
.\.venv\Scripts\Activate.ps1     
```
4.1 Your shell should look something like this
```
(.venv) PS D:\<location>\PenguBot>
```
5. Install requirements
```
pip install -r requirements.txt  --prefer-binary
```
6. Install Pytorch Manually
```
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu118
```
