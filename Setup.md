# Step by Step Setup Guide PENGUBOT

1. Clone the Repo
```powershell
git clone https://github.com/stormcoph/PenguBot
```

2. cd into it
```powershell
cd PenguBot
```

3. Create venv 
```powershell
py -3.11 -m venv .venv 
```

4. Activate venv
```powershell
&".\.venv\Scripts\Activate.ps1" 
```

  4.1 Your shell should look something like this
```powershell
(.venv) PS D:\<location>\PenguBot>
```

5. Install requirements
```powershell
pip install -r requirements.txt  --prefer-binary
```
5.1 Install Cuda with winget and Follow the Installer 
```shell
winget install Nvidia.CUDA -v 11.8 -i --force
```

6. Install Pytorch Manually -> This may take a while
```powershell
pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu118
```

7. Restart your Computer