# AWS Wickr Data Retention Analysis Solution

This guide will describe the process of deploying and configuring the [AWS Wickr Data Retention service](https://docs.aws.amazon.com/wickr/latest/adminguide/data-retention.html) to use Amazon Kinesis Data Firehose to stream data retention logs to Amazon S3, and then to use Amazon Athena to query the logs. 

This template will build the following;

 - An Amazon S3 Bucket where your messages will be sent to by the AWS Wickr Data retention service.
 - An Amazon EC2 instance that will run your data retention service. Docker CE has been pre-installed along with the retention image already pulled.
 - An AWS Secrets Manager secret, pre-populated with the required variables needed to deploy the service.
 - An AWS KMS Keys for encryption of your messages and files on S3.
 - An Amazon Kinesis Data Firehose with an S3 bucket set as the destination.
 - An AWS Glue Crawler, to create a schema from the retention data.
 - An Amazon Athena workgroup with an S3 bucket set for query output.
 - An AWS Lambda function that you can use (optionally) to automate the querying of Amazon Athena.

AWS KMS is used throughout to ensure data is stored securely at rest.

## Prerequisites and limitations

## Prerequisites

- Administrative access to the AWS Wickr network management panel.
- A user running the AWS Wickr client on a device, and at least one other user able to exchange messages with.
- A username and the initial password for the data retention service.
- Familiarity with Linux text editors. Vim is used for this sample but others can be installed and used.

## Limitations

- This solution requires ~1Mb of data to be sent through your clients to push the data to S3. To generate data in the Wickr client, you can copy+paste some data from [Lorus Ipsum.](https://www.lipsum.com/feed/html)

## Architecture

The following diagram illustrates the resources deployed

![architecture](images/architecture.png?raw=true)
 
AWS Wickr retention data is first streamed via the Amazon Kinesis Agent to an Amazon S3 bucket once a new message is added to the retention message file. From there, you will use an AWS Glue crawler to create a table based on the retention data fields, and finally used Amazon Athena to query that data. Additionally, raw retention data is sent to a separate S3 bucket once the retention file reaches 1KB in size.

## Tools

- The AWS Wickr Client - Installation instructions sent on invite email.

## Configure AWS Wickr Data Retention

1. Clone this repo and in the same folder as `cloudformation.yaml` run the following add the `--region` flag to deploy to an alternate region from your default:
```
aws cloudformation deploy --stack-name wickr-retention --template-file cloudformation.yaml --capabilities=CAPABILITY_IAM
```
2. Go to the AWS Secrets Manager console, and into the secret that has been created for you called `data-retention`
3. Edit the secret value for the **'password'** key, paste in the compliance service password and click Save. **NOTE:** Ensure you remove any whitespace from the front of the password!
4. Go to the Amazon EC2 management console, select the **'retention'** instance and click **'Connect'** on the top-right of the screen.
5. Select the **'Session Manager'** tab and then **'Connect'.**
6. At the command prompt, switch into the ec2-user user `sudo su - ec2-user`
7. Now, replacing the `<compliance_bot_username>` parameter with the one saved earlier, run the following command:
```
docker run -v /opt/<compliance_bot_username>:/tmp/<compliance_bot_username> -d --restart on-failure:5 --name="<compliance_bot_username>" -ti -e WICKRIO_BOT_NAME='<compliance_bot_username>' -e AWS_SECRET_NAME='data-retention' -e WICKRIO_COMP_FILESIZE='1000' wickr/bot-compliance-cloud:latest
```
8. Now to ensure the service has started correctly, run `docker ps -a` and copy the Container ID, then run `docker logs <container_ID`. You should see Login Successful and a new password. 
9. Repeat step 2 and 3, and replace the initial password with this new one. This will be used if you restart the retention service.
10. Go to the AWS Wickr Network admin pane, under **'Data Retention'** and ensure you now have a green tick at the bottom, then switch the toggle at the bottom to on.
12. The **data retention** title at the top of the page will now have a green Active icon next to it. You are now running Data retention for your network.

## Configure the Amazon Kinesis Data Firehose Agent

1. Return to the EC2 Session Manager console for your retention instance.
2. Switch back into the ec2-user by running `sudo su - ec2-user`
3. Replace the contents of `/etc/aws-kinesis/agent.json` with the following, ensuring to replace the retention bot username with the one that you are using:
```json
{
  "cloudwatch.emitMetrics": false,
  "flows": [
    {
      "filePattern": "/opt/<compliance_bot_username>/compliance/messages/*.txt",
      "deliveryStream": "wickr-data-retention"
    }
  ]
}
```
4. Save and exit the file.
5. Start the Kinesis agent by running `sudo service aws-kinesis-agent start`
6. Make the Kinesis agent start on system reboot by running `sudo chkconfig aws-kinesis-agent on`
7. You can view the log file for the agent by following the Kinesis agent logs file with `tail -f /var/log/aws-kinesis-agent/aws-kinesis-agent.log`
8. At this point it is a good idea to send a few messages using your Wickr client. These messages will soon start to appear in the S3 bucket called 'kinesis-data-*'.

## Run AWS Glue Crawler

1. Go to the AWS Glue management console.
2. Select **'Crawlers'** from the left hand side, under the **Data Catalog** heading.
3. Select the **wickr-crawler** crawler and then press **'Run'**.
4. Once the crawler is complete, you will see an entry in the 'Table changes since last run' column.
5. Select **'Tables'** from the left hand side, and then select the table that you see in the panel.
6. You will now be able to see the schema that AWS Glue has created, based on the data in your retention S3 bucket.

## Query with Amazon Athena

1. Go to the Amazon Athena management console and select **'Explore the query editor.'**
2. On the **'Workgroup'** drop down selection on the right hand side, select **wickr** and then **Acknowledge** that Workgroup settings pop-up.
3. From here you can run a few simple queries to get started exploring your data. To show all messages from your retention instance, run:
```
SELECT * FROM <table-name>;
```
Where 'table name' is shown on the left-hand side window.

To show all messages sent to a certain user-id, and ordered by time, you could run the following;
```
SELECT * FROM <table-name> WHERE sender='username@domain.com' ORDER BY time DESC
```
4. If required, you can download these results by selecting **'Download results'** on the left hand side (.csv format).

# Optional Further Steps

## Use an Amazon EventBridge Rule to trigger an AWS Lambda Function

- You can use an Amazon Athena query on a timed schedule and have the subsequent output file sent to an S3 bucket of your choice. The **athena-query-lambda.py** function can be modified to your needs and then attached to a rule. See this [link](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html) for instructions on how to create an Amazon EventBridge rule that runs on a schedule, and from there have it trigger the Lambda function.

# Additional Information

To delete this solution, run aws `cloudformation delete-stack --stack-name wickr-retention`. You will need to manually empty and then delete the S3 buckets created by this solution.


