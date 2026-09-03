# Deploy with CloudFormation (CLI)

This document explains how to launch the voting app with **AWS CloudFormation** and the **AWS CLI**.


## Prerequisites

You need the **AWS CLI** installed and configured with current AWS Academy Learner Lab credentials in the `[default]` profile.


## One-Time Setup

The file file `deploy/userdata.sh` is used in the deployment process, and you must change one line before you deploy

* Open `deploy/userdata.sh` in Cursor or `nano`.
* Near the top of the file you will find the line:

  ```
  REPO_URL="https://github.com/YOUR_GITHUB_USERNAME/voting_monolith.git"
  ```
* Change `YOUR_GITHUB_USERNAME` to your Github username.
* Commit this change to the git repo, and push it back to your Github account

  ```
  git add deploy/userdata.sh
  git commit -m "set github account"
  git push origin main
  ```
  
If the `git push` command fails, check the url of `origin` and make sure it points at your fork of the repo

  ```
  git remote -v
  ```
  


## Create the stack

CloudFormation defines a *stack* of AWS resources. For this application we need:

* A security group that allows SSH, HTTP, and HTTPS
* The EC2 instance

The file `deploy/cloudformation.yaml` specifies those resources. 

From the root of your clone:

```bash
aws cloudformation create-stack \
  --stack-name voting-monolith \
  --template-body file://deploy/cloudformation.yaml \
  --parameters ParameterKey=GitHubUsername,ParameterValue=YOUR_GITHUB_USERNAME
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub username.

Wait until the stack finished creating:

```bash
aws cloudformation wait stack-create-complete \
  --stack-name voting-monolith
```

## After the stack is complete

Read the public IP from the stack output:

```bash
aws cloudformation describe-stacks \
  --stack-name voting-monolith \
  --query 'Stacks[0].Outputs' \
  --output table
```

**CREATE_COMPLETE does not mean the app is ready.** User data still installs packages, clones the repo, and starts services. Wait a few minutes, then:

```bash
curl -s http://PUBLIC_IP/health
```

Or SSH with your Academy key and check `/var/log/cloud-init-output.log` if something failed.

If you use an Elastic IP for the semester, **associate it** with this instance in the EC2 console (or with the CLI) after the instance exists, then use that address instead of the ephemeral public IP.

## Delete the stack

When you are done with the resources this template created:

```bash
aws cloudformation delete-stack --stack-name voting-monolith
aws cloudformation wait stack-delete-complete --stack-name voting-monolith
```

Deleting the stack removes the instance and the security group. It does **not** release an Elastic IP you associated by hand.
