import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DescribeReceiptRuleRequest, DescribeReceiptRuleResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DescribeReceiptRuleCommand}.
 */
export interface DescribeReceiptRuleCommandInput extends DescribeReceiptRuleRequest {
}
/**
 * @public
 *
 * The output of {@link DescribeReceiptRuleCommand}.
 */
export interface DescribeReceiptRuleCommandOutput extends DescribeReceiptRuleResponse, __MetadataBearer {
}
declare const DescribeReceiptRuleCommand_base: {
    new (input: DescribeReceiptRuleCommandInput): import("@smithy/smithy-client").CommandImpl<DescribeReceiptRuleCommandInput, DescribeReceiptRuleCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DescribeReceiptRuleCommandInput): import("@smithy/smithy-client").CommandImpl<DescribeReceiptRuleCommandInput, DescribeReceiptRuleCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns the details of the specified receipt rule.</p>
 *          <p>For information about setting up receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DescribeReceiptRuleCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DescribeReceiptRuleCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DescribeReceiptRuleRequest
 *   RuleSetName: "STRING_VALUE", // required
 *   RuleName: "STRING_VALUE", // required
 * };
 * const command = new DescribeReceiptRuleCommand(input);
 * const response = await client.send(command);
 * // { // DescribeReceiptRuleResponse
 * //   Rule: { // ReceiptRule
 * //     Name: "STRING_VALUE", // required
 * //     Enabled: true || false,
 * //     TlsPolicy: "Require" || "Optional",
 * //     Recipients: [ // RecipientsList
 * //       "STRING_VALUE",
 * //     ],
 * //     Actions: [ // ReceiptActionsList
 * //       { // ReceiptAction
 * //         S3Action: { // S3Action
 * //           TopicArn: "STRING_VALUE",
 * //           BucketName: "STRING_VALUE", // required
 * //           ObjectKeyPrefix: "STRING_VALUE",
 * //           KmsKeyArn: "STRING_VALUE",
 * //           IamRoleArn: "STRING_VALUE",
 * //         },
 * //         BounceAction: { // BounceAction
 * //           TopicArn: "STRING_VALUE",
 * //           SmtpReplyCode: "STRING_VALUE", // required
 * //           StatusCode: "STRING_VALUE",
 * //           Message: "STRING_VALUE", // required
 * //           Sender: "STRING_VALUE", // required
 * //         },
 * //         WorkmailAction: { // WorkmailAction
 * //           TopicArn: "STRING_VALUE",
 * //           OrganizationArn: "STRING_VALUE", // required
 * //         },
 * //         LambdaAction: { // LambdaAction
 * //           TopicArn: "STRING_VALUE",
 * //           FunctionArn: "STRING_VALUE", // required
 * //           InvocationType: "Event" || "RequestResponse",
 * //         },
 * //         StopAction: { // StopAction
 * //           Scope: "RuleSet", // required
 * //           TopicArn: "STRING_VALUE",
 * //         },
 * //         AddHeaderAction: { // AddHeaderAction
 * //           HeaderName: "STRING_VALUE", // required
 * //           HeaderValue: "STRING_VALUE", // required
 * //         },
 * //         SNSAction: { // SNSAction
 * //           TopicArn: "STRING_VALUE", // required
 * //           Encoding: "UTF-8" || "Base64",
 * //         },
 * //         ConnectAction: { // ConnectAction
 * //           InstanceARN: "STRING_VALUE", // required
 * //           IAMRoleARN: "STRING_VALUE", // required
 * //         },
 * //       },
 * //     ],
 * //     ScanEnabled: true || false,
 * //   },
 * // };
 *
 * ```
 *
 * @param DescribeReceiptRuleCommandInput - {@link DescribeReceiptRuleCommandInput}
 * @returns {@link DescribeReceiptRuleCommandOutput}
 * @see {@link DescribeReceiptRuleCommandInput} for command's `input` shape.
 * @see {@link DescribeReceiptRuleCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link RuleDoesNotExistException} (client fault)
 *  <p>Indicates that the provided receipt rule does not exist.</p>
 *
 * @throws {@link RuleSetDoesNotExistException} (client fault)
 *  <p>Indicates that the provided receipt rule set does not exist.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example DescribeReceiptRule
 * ```javascript
 * // The following example returns the details of a receipt rule:
 * const input = {
 *   RuleName: "MyRule",
 *   RuleSetName: "MyRuleSet"
 * };
 * const command = new DescribeReceiptRuleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   Rule: {
 *     Actions: [
 *       {
 *         S3Action: {
 *           BucketName: "MyBucket",
 *           ObjectKeyPrefix: "email"
 *         }
 *       }
 *     ],
 *     Enabled: true,
 *     Name: "MyRule",
 *     ScanEnabled: true,
 *     TlsPolicy: "Optional"
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class DescribeReceiptRuleCommand extends DescribeReceiptRuleCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DescribeReceiptRuleRequest;
            output: DescribeReceiptRuleResponse;
        };
        sdk: {
            input: DescribeReceiptRuleCommandInput;
            output: DescribeReceiptRuleCommandOutput;
        };
    };
}
