from troposphere import Template, Parameter, Ref, Select, GetAtt, Output, Join
import troposphere.awslambda as awslambda
import troposphere.iam as iam
t = Template()
t.add_description("SSM logs from S3 to Lambda to SNS")
t.add_version("2010-09-09")

lambda_code_package = t.add_parameter(Parameter(
    "LambdaCodePackage",
    Type="CommaDelimitedList",
    Default="s3bucketname,key",
    Description="bucketname,bucketpath",
))
sns_topic = t.add_parameter(Parameter(
    "snsTopic",
    Default="",
    Type="String",
    Description = "SNS topic ARN to which lambda outputs the logs"
))
ssm_s3_bucket = t.add_parameter(Parameter(
    "ssmS3Bucket",
    Default="ssmS3LogsToSNS",
    Type="String",
    Description="Input bucket where lambda will get the SSM logs from"
))

role = t.add_resource(iam.Role(
    "lambdaSsmS3SnsAccessRole",
    AssumeRolePolicyDocument={
        "Version": "2012-10-17",
        "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
      ]
    },
    Policies=[
        iam.Policy(
            PolicyName="LambdaLogPolicy",
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "arn:aws:logs:*:*:*"
                    }
                ]
            }
        ),
        iam.Policy(
            PolicyName="LambdaSNSPublishPolicy",
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": [
                            "sns:Publish"
                        ],
                        "Effect": "Allow",
                        "Resource": Join("",["arn:aws:sns:", Ref(sns_topic)])
                    }
                ]
            }
        ),
        iam.Policy(
            PolicyName="LambdaGetObjectFromS3Policy",
            PolicyDocument={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": [
                            "s3:GetObject"
                        ],
                        "Effect": "Allow",
                        "Resource": Join("",["arn:aws:s3:::", Ref(ssm_s3_bucket), "*"])
                    }
                ]
            }
        ),
    ]
))

func = t.add_resource(awslambda.Function(
    "SsmLogsFromS3ToSnsLambda",
    Code=awslambda.Code(
        S3Bucket=Select(0,Ref(lambda_code_package)),
        S3Key=Select(1,Ref(lambda_code_package))
    ),
    FunctionName="SsmLogsFromS3ToSnsLambda",
    Handler="main.handler",
    Role=GetAtt(role,"Arn"),
    Runtime="python2.7",
    Timeout=300,
))

t.add_output(Output(
    "FunctionArn",
    Value=GetAtt(func,"Arn")
))

t.add_output(Output(
    "lambdaSsmS3SnsAccessRole",
    Value=GetAtt(role,"Arn")
))

print t.to_json()