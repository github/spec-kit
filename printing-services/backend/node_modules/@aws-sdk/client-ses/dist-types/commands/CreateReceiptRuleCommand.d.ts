import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { CreateReceiptRuleRequest, CreateReceiptRuleResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateReceiptRuleCommand}.
 */
export interface CreateReceiptRuleCommandInput extends CreateReceiptRuleRequest {
}
/**
 * @public
 *
 * The output of {@link CreateReceiptRuleCommand}.
 */
export interface CreateReceiptRuleCommandOutput extends CreateReceiptRuleResponse, __MetadataBearer {
}
declare const CreateReceiptRuleCommand_base: {
    new (input: CreateReceiptRuleCommandInput): import("@smithy/smithy-client").CommandImpl<CreateReceiptRuleCommandInput, CreateReceiptRuleCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: CreateReceiptRuleCommandInput): import("@smithy/smithy-client").CommandImpl<CreateReceiptRuleCommandInput, CreateReceiptRuleCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Creates a receipt rule.</p>
 *          <p>For information about setting up receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, CreateReceiptRuleCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, CreateReceiptRuleCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // CreateReceiptRuleRequest
 *   RuleSetName: "STRING_VALUE", // required
 *   After: "STRING_VALUE",
 *   Rule: { // ReceiptRule
 *     Name: "STRING_VALUE", // required
 *     Enabled: true || false,
 *     TlsPolicy: "Require" || "Optional",
 *     Recipients: [ // RecipientsList
 *       "STRING_VALUE",
 *     ],
 *     Actions: [ // ReceiptActionsList
 *       { // ReceiptAction
 *         S3Action: { // S3Action
 *           TopicArn: "STRING_VALUE",
 *           BucketName: "STRING_VALUE", // required
 *           ObjectKeyPrefix: "STRING_VALUE",
 *           KmsKeyArn: "STRING_VALUE",
 *           IamRoleArn: "STRING_VALUE",
 *         },
 *         BounceAction: { // BounceAction
 *           TopicArn: "STRING_VALUE",
 *           SmtpReplyCode: "STRING_VALUE", // required
 *           StatusCode: "STRING_VALUE",
 *           Message: "STRING_VALUE", // required
 *           Sender: "STRING_VALUE", // required
 *         },
 *         WorkmailAction: { // WorkmailAction
 *           TopicArn: "STRING_VALUE",
 *           OrganizationArn: "STRING_VALUE", // required
 *         },
 *         LambdaAction: { // LambdaAction
 *           TopicArn: "STRING_VALUE",
 *           FunctionArn: "STRING_VALUE", // required
 *           InvocationType: "Event" || "RequestResponse",
 *         },
 *         StopAction: { // StopAction
 *           Scope: "RuleSet", // required
 *           TopicArn: "STRING_VALUE",
 *         },
 *         AddHeaderAction: { // AddHeaderAction
 *           HeaderName: "STRING_VALUE", // required
 *           HeaderValue: "STRING_VALUE", // required
 *         },
 *         SNSAction: { // SNSAction
 *           TopicArn: "STRING_VALUE", // required
 *           Encoding: "UTF-8" || "Base64",
 *         },
 *         ConnectAction: { // ConnectAction
 *           InstanceARN: "STRING_VALUE", // required
 *           IAMRoleARN: "STRING_VALUE", // required
 *         },
 *       },
 *     ],
 *     ScanEnabled: true || false,
 *   },
 * };
 * const command = new CreateReceiptRuleCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param CreateReceiptRuleCommandInput - {@link CreateReceiptRuleCommandInput}
 * @returns {@link CreateReceiptRuleCommandOutput}
 * @see {@link CreateReceiptRuleCommandInput} for command's `input` shape.
 * @see {@link CreateReceiptRuleCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link AlreadyExistsException} (client fault)
 *  <p>Indicates that a resource could not be created because of a naming conflict.</p>
 *
 * @throws {@link InvalidLambdaFunctionException} (client fault)
 *  <p>Indicates that the provided Amazon Web Services Lambda function is invalid, or that Amazon SES could
 *             not execute the provided function, possibly due to permissions issues. For information
 *             about giving permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *
 * @throws {@link InvalidS3ConfigurationException} (client fault)
 *  <p>Indicates that the provided Amazon S3 bucket or Amazon Web Services KMS encryption key is invalid,
 *             or that Amazon SES could not publish to the bucket, possibly due to permissions issues.
 *             For information about giving permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *
 * @throws {@link InvalidSnsTopicException} (client fault)
 *  <p>Indicates that the provided Amazon SNS topic is invalid, or that Amazon SES could not
 *             publish to the topic, possibly due to permissions issues. For information about giving
 *             permissions, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/receiving-email-permissions.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *
 * @throws {@link LimitExceededException} (client fault)
 *  <p>Indicates that a resource could not be created because of service limits. For a list
 *             of Amazon SES limits, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/limits.html">Amazon SES Developer
 *             Guide</a>.</p>
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
 * @example CreateReceiptRule
 * ```javascript
 * // The following example creates a new receipt rule:
 * const input = {
 *   After: "",
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
 *   },
 *   RuleSetName: "MyRuleSet"
 * };
 * const command = new CreateReceiptRuleCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class CreateReceiptRuleCommand extends CreateReceiptRuleCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: CreateReceiptRuleRequest;
            output: {};
        };
        sdk: {
            input: CreateReceiptRuleCommandInput;
            output: CreateReceiptRuleCommandOutput;
        };
    };
}
