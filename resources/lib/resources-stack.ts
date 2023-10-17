import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { Table, BillingMode, AttributeType, StreamViewType } from 'aws-cdk-lib/aws-dynamodb';
import { Function, Runtime, Code, StartingPosition } from 'aws-cdk-lib/aws-lambda';
import { DynamoEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';
import { Domain, EngineVersion,  } from 'aws-cdk-lib/aws-opensearchservice';
import { EbsDeviceVolumeType, } from 'aws-cdk-lib/aws-ec2';



export class ResourcesStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const userTable = new Table(this, "UserTable", {
      tableName: "user-table-opensearch",
      billingMode: BillingMode.PAY_PER_REQUEST,
      partitionKey: {name: "partitionKey", type: AttributeType.STRING},
      sortKey: {name: "sortKey", type: AttributeType.STRING},
      pointInTimeRecovery: true,
      stream: StreamViewType.NEW_IMAGE // This is the important line!
    });

    const userTableIndexingFunction = new Function(this, "UserTableIndexingFunction", {
      code: Code.fromAsset("lambda"),
      runtime: Runtime.PYTHON_3_10,
      handler: "app.handler",
      timeout: cdk.Duration.seconds(30),
    });

    userTableIndexingFunction.addEventSource(new DynamoEventSource(userTable, {
      startingPosition: StartingPosition.TRIM_HORIZON,
      batchSize: 1,
      retryAttempts: 3
    }));

  //   const openSearchDomain = new Domain(this, "OpenSearchDomain", {
  //     version: EngineVersion.OPENSEARCH_1_0,
  //   capacity: {dataNodeInstanceType: "t3.small.search",
  //     dataNodes: 1,
  //     masterNodes: 0
  //   },
  //   ebs: {enabled: true,
  //     volumeSize: 50,
  //     volumeType: EbsDeviceVolumeType.GENERAL_PURPOSE_SSD
  //   },
  //   logging: {slowSearchLogEnabled: true,
  //     appLogEnabled: true,
  //     slowIndexLogEnabled: true,
  //   },
  // });

  // openSearchDomain.grantIndexReadWrite("user-index", userTableIndexingFunction);
  }
}
