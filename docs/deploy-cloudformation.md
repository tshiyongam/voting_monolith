# Deploy with CloudFormation (CLI)

This document explains how to launch the voting app with **AWS CloudFormation** and the **AWS CLI**. The template creates a small **public VPC**, a `t3.micro` Amazon Linux instance, a security group (ports **22**, **80**, and **443** from anywhere), and a short user-data stub that downloads `deploy/userdata.sh` from **your** GitHub fork and runs it.

The key pair name is **`vockey`** (the usual AWS Academy key). You only pass your **GitHub username** as a parameter.

Template file: `deploy/cloudformation.yaml`.

## Set up the AWS CLI

This section assumes the AWS CLI is already installed on your **Mac**. You still need credentials from **AWS Academy Learner Lab** for each lab session.

### 1. Start the lab and copy CLI credentials

1. Start your **Learner Lab** and wait until it is ready (green indicator).
2. Open **AWS Details**.
3. Next to **AWS CLI**, choose **Show**.
4. Copy the credential block Academy displays. It includes a temporary access key, secret access key, and session token for the `[default]` profile.

Those credentials expire when the lab session ends (on the order of a few hours). Copy a fresh block at the start of each session.

### 2. Write `~/.aws/credentials`

```bash
mkdir -p ~/.aws
```

Put Academy’s block into `~/.aws/credentials`. It should look like this (use the **values from the lab**, not these placeholders):

```ini
[default]
aws_access_key_id=ASIA...
aws_secret_access_key=...
aws_session_token=...
```

You can replace the whole file with what Academy shows, or paste under `[default]` if you keep other named profiles for other work.

### 3. Write `~/.aws/config`

Create `~/.aws/config` with your lab region. AWS Academy Learner Lab is normally **`us-east-1`**:

```ini
[default]
region=us-east-1
output=json
```

`output=json` is optional; it makes CLI output easier to read in scripts.

### 4. Check that the CLI works

```bash
aws sts get-caller-identity
```

You should see an account id and an ARN for the lab role (not an error about missing credentials). If authentication fails, start the lab again, copy a new credential block, and update `~/.aws/credentials`.

## Before you create the stack

1. In your fork, set **`REPO_URL`** in `deploy/userdata.sh` to your clone URL (keep the repository name **`voting_monolith`**).
2. **Commit and push** that change to **`main`**. The instance downloads the script from GitHub at boot; an unpushed edit will not be used.
3. Configure the AWS CLI with current Learner Lab credentials (see [Set up the AWS CLI](#set-up-the-aws-cli)).
4. Confirm the template is valid (optional but useful):

```bash
aws cloudformation validate-template \
  --template-body file://deploy/cloudformation.yaml
```

Run that command from the **root of your clone** (so the `file://` path is correct).

## Create the stack

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

Read the outputs (public IP and health URL):

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

Deleting the stack removes the instance, security group, and the VPC (and related networking) created by the template. It does **not** release an Elastic IP you associated by hand.
