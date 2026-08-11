# Deploy on EC2

This document explains how to run the monolithic voting app on an EC2 instance. It uses **DynamoDB Local** for the database and **gunicorn** for the web process; both run under **systemd**. The app listens on port **80**. Code and data live under `/home/ec2-user/voting_monolith`.

You deploy with one root script, `deploy/userdata.sh`. It installs packages, clones your fork, sets up the app, starts DynamoDB Local, creates the `Polls` table, and starts gunicorn.

## One-Time Action

In your copy of the repo, set **`REPO_URL`** in `deploy/userdata.sh` to your repo's clone URL.  NOTE:  Other files in this project assume the project name is `voting_monolith`, so make sure your repo name matches.

## Deploy Process

The file `deploy/userdata.sh` contains all the commands needed to deploy the application.  It will:

* Install necessary packages
* Clone the repo
* Setup the `.venv`
* Use the example `.env` file for configuration
* Download DynamoDB Local
* Setup systemd services for DynamoDB Local and Gunicorn
* Launch DynamoDB
* Create the table
* Launch Gunicorn

We will use the [cloud-init feature of EC2 with `userdat`](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html#userdata-linux) when we launch the instance:

In the Launch dialog:

* (Optional) Name the instance
* Use the default `t3.micro` instance type
* Select your `vockey` for authentication
* Ensure that HTTP and SSH are enabled in the security group
* Under "Advanced", paste the contents of `deploy/userdata.sh` into **User data**

When you launch the instance, AWS will boot the instance, and then run the userdata script.  This may take a minute or two, and once it completes DynamoDB Local and Gunicorn will be running (i.e. the app will be deployed).

## Debugging

Cloud-init logs all output of the userdata script to `/var/log/cloud-init-output.log`.  If the app does not start, SSH to the instance and look at this file to understand what failed.


## Other Useful Commands on the EC2 Instance

- `systemctl status voting` — see the status of the Gunicorn process
- `systemctl status dynamodb-local` — see the status of the DynamoDB Local process
- `curl -s http://localhost/health` — make a call to the `/health` endpoint, which returns a 200-status code if the web server is running and it can communicate with DynamoDB Local
- `sudo systemctl restart voting` — restart the web process after a config or code change
- `sudo journalctl -u voting -f` — follow the voting (gunicorn) logs
- `sudo journalctl -u dynamodb-local -f` — follow the DynamoDB Local logs
