# ticket-threader
An external message threader for redmine


## development

### setting up

```
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install IMAPClient
pip install python-dotenv
pip install requests
pip freeze > requirements.txt
```

## operation

### running

```
./threader.py
```