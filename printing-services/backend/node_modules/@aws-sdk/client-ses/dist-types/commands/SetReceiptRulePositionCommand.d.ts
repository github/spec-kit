import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SetReceiptRulePositionRequest, SetReceiptRulePositionResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link SetReceiptRulePositionCommand}.
 */
export interface SetReceiptRulePositionCommandInput extends SetReceiptRulePositionRequest {
}
/**
 * @public
 *
 * The output of {@link SetReceiptRulePositionCommand}.
 */
export interface SetReceiptRulePositionCommandOutput extends SetReceiptRulePositionResponse, __MetadataBearer {
}
declare const SetReceiptRulePositionCommand_base: {
    new (input: SetReceiptRulePositionCommandInput): import("@smithy/smithy-client").CommandImpl<SetReceiptRulePositionCommandInput, SetReceiptRulePositionCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: SetReceiptRulePositionCommandInput): import("@smithy/smithy-client").CommandImpl<SetReceiptRulePositionCommandInput, SetReceiptRulePositionCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Sets the position of the specified receipt rule in the receipt rule set.</p>
 *          <p>For information about managing receipt rules, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, SetReceiptRulePositionCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, SetReceiptRulePositionCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // SetReceiptRulePositionRequest
 *   RuleSetName: "STRING_VALUE", // required
 *   RuleName: "STRING_VALUE", // required
 *   After: "STRING_VALUE",
 * };
 * const command = new SetReceiptRulePositionCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param SetReceiptRulePositionCommandInput - {@link SetReceiptRulePositionCommandInput}
 * @returns {@link SetReceiptRulePositionCommandOutput}
 * @see {@link SetReceiptRulePositionCommandInput} for command's `input` shape.
 * @see {@link SetReceiptRulePositionCommandOutput} for command's `response` shape.
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
 * @example SetReceiptRulePosition
 * ```javascript
 * // The following example sets the position of a receipt rule in a receipt rule set:
 * const input = {
 *   After: "PutRuleAfterThisRule",
 *   RuleName: "RuleToReposition",
 *   RuleSetName: "MyRuleSet"
 * };
 * const command = new SetReceiptRulePositionCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class SetReceiptRulePositionCommand extends SetReceiptRulePositionCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: SetReceiptRulePositionRequest;
            output: {};
        };
        sdk: {
            input: SetReceiptRulePositionCommandInput;
            output: SetReceiptRulePositionCommandOutput;
        };
    };
}
