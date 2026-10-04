# Overview


### Setup

#### Cloning Repo
Navigate to a local directory where you would like to clone this repo, such as in a repos directory, which the following instructions will assume

```
cd repos

git clone https://github.com/rya000667/public-fantast-football-analytics.git

cd public-fantast-football-analytics
```

#### Setting up Local Development Environment
In the root of the repo from above, we will setup a virtual environment.  There are many ways to do this, this approach will demonstrate using pythons built in venv module and assume that your operating system has python configured as 'python'.  Note there are other means to configure such as py3, python3, etc.  If that is the case, replace python below with what you have configured.  Also, we will name the local virtual environment .venv, feel free to replace with your preferred name.

```
python -m venv .venv
# to validate success, you should now see the command line as (.venv)

# install requirements
pip -r requirements.txt
```





