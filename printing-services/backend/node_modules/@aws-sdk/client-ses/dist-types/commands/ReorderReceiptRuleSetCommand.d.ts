import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ReorderReceiptRuleSetRequest, ReorderReceiptRuleSetResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ReorderReceiptRuleSetCommand}.
 */
export interface ReorderReceiptRuleSetCommandInput extends ReorderReceiptRuleSetRequest {
}
/**
 * @public
 *
 * The output of {@link ReorderReceiptRuleSetCommand}.
 */
export interface ReorderReceiptRuleSetCommandOutput extends ReorderReceiptRuleSetResponse, __MetadataBearer {
}
declare const ReorderReceiptRuleSetCommand_base: {
    new (input: ReorderReceiptRuleSetCommandInput): import("@smithy/smithy-client").CommandImpl<ReorderReceiptRuleSetCommandInput, ReorderReceiptRuleSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: ReorderReceiptRuleSetCommandInput): import("@smithy/smithy-client").CommandImpl<ReorderReceiptRuleSetCommandInput, ReorderReceiptRuleSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Reorders the receipt rules within a receipt rule set.</p>
 *          <note>
 *             <p>All of the rules in the rule set must be represented in this request. That is, it
 *                 is error if the reorder request doesn't explicitly position all of the rules.</p>
 *          </note>
 *          <p>For information about managing receipt rule sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, ReorderReceiptRuleSetCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ReorderReceiptRuleSetCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // ReorderReceiptRuleSetRequest
 *   RuleSetName: "STRING_VALUE", // required
 *   RuleNames: [ // ReceiptRuleNamesList // required
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new ReorderReceiptRuleSetCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param ReorderReceiptRuleSetCommandInput - {@link ReorderReceiptRuleSetCommandInput}
 * @returns {@link ReorderReceiptRuleSetCommandOutput}
 * @see {@link ReorderReceiptRuleSetCommandInput} for command's `input` shape.
 * @see {@link ReorderReceiptRuleSetCommandOutput} for command's `response` shape.
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
 * @example ReorderReceiptRuleSet
 * ```javascript
 * // The following example reorders the receipt rules within a receipt rule set:
 * const input = {
 *   RuleNames: [
 *     "MyRule",
 *     "MyOtherRule"
 *   ],
 *   RuleSetName: "MyRuleSet"
 * };
 * const command = new ReorderReceiptRuleSetCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class ReorderReceiptRuleSetCommand extends ReorderReceiptRuleSetCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: ReorderReceiptRuleSetRequest;
            output: {};
        };
        sdk: {
            input: ReorderReceiptRuleSetCommandInput;
            output: ReorderReceiptRuleSetCommandOutput;
        };
    };
}
