import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DescribeActiveReceiptRuleSetRequest, DescribeActiveReceiptRuleSetResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DescribeActiveReceiptRuleSetCommand}.
 */
export interface DescribeActiveReceiptRuleSetCommandInput extends DescribeActiveReceiptRuleSetRequest {
}
/**
 * @public
 *
 * The output of {@link DescribeActiveReceiptRuleSetCommand}.
 */
export interface DescribeActiveReceiptRuleSetCommandOutput extends DescribeActiveReceiptRuleSetResponse, __MetadataBearer {
}
declare const DescribeActiveReceiptRuleSetCommand_base: {
    new (input: DescribeActiveReceiptRuleSetCommandInput): import("@smithy/smithy-client").CommandImpl<DescribeActiveReceiptRuleSetCommandInput, DescribeActiveReceiptRuleSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [DescribeActiveReceiptRuleSetCommandInput]): import("@smithy/smithy-client").CommandImpl<DescribeActiveReceiptRuleSetCommandInput, DescribeActiveReceiptRuleSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns the metadata and receipt rules for the receipt rule set that is currently
 *             active.</p>
 *          <p>For information about setting up receipt rule sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-concepts.html#receiving-email-concepts-rules">Amazon SES Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DescribeActiveReceiptRuleSetCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DescribeActiveReceiptRuleSetCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = {};
 * const command = new DescribeActiveReceiptRuleSetCommand(input);
 * const response = await client.send(command);
 * // { // DescribeActiveReceiptRuleSetResponse
 * //   Metadata: { // ReceiptRuleSetMetadata
 * //     Name: "STRING_VALUE",
 * //     CreatedTimestamp: new Date("TIMESTAMP"),
 * //   },
 * //   Rules: [ // ReceiptRulesList
 * //     { // ReceiptRule
 * //       Name: "STRING_VALUE", // required
 * //       Enabled: true || false,
 * //       TlsPolicy: "Require" || "Optional",
 * //       Recipients: [ // RecipientsList
 * //         "STRING_VALUE",
 * //       ],
 * //       Actions: [ // ReceiptActionsList
 * //         { // ReceiptAction
 * //           S3Action: { // S3Action
 * //             TopicArn: "STRING_VALUE",
 * //             BucketName: "STRING_VALUE", // required
 * //             ObjectKeyPrefix: "STRING_VALUE",
 * //             KmsKeyArn: "STRING_VALUE",
 * //             IamRoleArn: "STRING_VALUE",
 * //           },
 * //           BounceAction: { // BounceAction
 * //             TopicArn: "STRING_VALUE",
 * //             SmtpReplyCode: "STRING_VALUE", // required
 * //             StatusCode: "STRING_VALUE",
 * //             Message: "STRING_VALUE", // required
 * //             Sender: "STRING_VALUE", // required
 * //           },
 * //           WorkmailAction: { // WorkmailAction
 * //             TopicArn: "STRING_VALUE",
 * //             OrganizationArn: "STRING_VALUE", // required
 * //           },
 * //           LambdaAction: { // LambdaAction
 * //             TopicArn: "STRING_VALUE",
 * //             FunctionArn: "STRING_VALUE", // required
 * //             InvocationType: "Event" || "RequestResponse",
 * //           },
 * //           StopAction: { // StopAction
 * //             Scope: "RuleSet", // required
 * //             TopicArn: "STRING_VALUE",
 * //           },
 * //           AddHeaderAction: { // AddHeaderAction
 * //             HeaderName: "STRING_VALUE", // required
 * //             HeaderValue: "STRING_VALUE", // required
 * //           },
 * //           SNSAction: { // SNSAction
 * //             TopicArn: "STRING_VALUE", // required
 * //             Encoding: "UTF-8" || "Base64",
 * //           },
 * //           ConnectAction: { // ConnectAction
 * //             InstanceARN: "STRING_VALUE", // required
 * //             IAMRoleARN: "STRING_VALUE", // required
 * //           },
 * //         },
 * //       ],
 * //       ScanEnabled: true || false,
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param DescribeActiveReceiptRuleSetCommandInput - {@link DescribeActiveReceiptRuleSetCommandInput}
 * @returns {@link DescribeActiveReceiptRuleSetCommandOutput}
 * @see {@link DescribeActiveReceiptRuleSetCommandInput} for command's `input` shape.
 * @see {@link DescribeActiveReceiptRuleSetCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example DescribeActiveReceiptRuleSet
 * ```javascript
 * // The following example returns the metadata and receipt rules for the receipt rule set that is currently active:
 * const input = { /* empty *\/ };
 * const command = new DescribeActiveReceiptRuleSetCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   Metadata: {
 *     CreatedTimestamp: "2016-07-15T16:25:59.607Z",
 *     Name: "default-rule-set"
 *   },
 *   Rules: [
 *     {
 *       Actions: [
 *         {
 *           S3Action: {
 *             BucketName: "MyBucket",
 *             ObjectKeyPrefix: "email"
 *           }
 *         }
 *       ],
 *       Enabled: true,
 *       Name: "MyRule",
 *       ScanEnabled: true,
 *       TlsPolicy: "Optional"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class DescribeActiveReceiptRuleSetCommand extends DescribeActiveReceiptRuleSetCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: {};
            output: DescribeActiveReceiptRuleSetResponse;
        };
        sdk: {
            input: DescribeActiveReceiptRuleSetCommandInput;
            output: DescribeActiveReceiptRuleSetCommandOutput;
        };
    };
}
