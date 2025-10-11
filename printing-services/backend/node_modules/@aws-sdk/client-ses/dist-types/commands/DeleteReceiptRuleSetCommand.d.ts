import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteReceiptRuleSetRequest, DeleteReceiptRuleSetResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteReceiptRuleSetCommand}.
 */
export interface DeleteReceiptRuleSetCommandInput extends DeleteReceiptRuleSetRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteReceiptRuleSetCommand}.
 */
export interface DeleteReceiptRuleSetCommandOutput extends DeleteReceiptRuleSetResponse, __MetadataBearer {
}
declare const DeleteReceiptRuleSetCommand_base: {
    new (input: DeleteReceiptRuleSetCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteReceiptRuleSetCommandInput, DeleteReceiptRuleSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteReceiptRuleSetCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteReceiptRuleSetCommandInput, DeleteReceiptRuleSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes the specified receipt rule set and all of the receipt rules it
 *             contains.</p>
 *          <note>
 *             <p>The currently active rule set cannot be deleted.</p>
 *          </note>
 *          <p>For information about managing receipt rule sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteReceiptRuleSetCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteReceiptRuleSetCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteReceiptRuleSetRequest
 *   RuleSetName: "STRING_VALUE", // required
 * };
 * const command = new DeleteReceiptRuleSetCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteReceiptRuleSetCommandInput - {@link DeleteReceiptRuleSetCommandInput}
 * @returns {@link DeleteReceiptRuleSetCommandOutput}
 * @see {@link DeleteReceiptRuleSetCommandInput} for command's `input` shape.
 * @see {@link DeleteReceiptRuleSetCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link CannotDeleteException} (client fault)
 *  <p>Indicates that the delete operation could not be completed.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example DeleteReceiptRuleSet
 * ```javascript
 * // The following example deletes a receipt rule set:
 * const input = {
 *   RuleSetName: "MyRuleSet"
 * };
 * const command = new DeleteReceiptRuleSetCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class DeleteReceiptRuleSetCommand extends DeleteReceiptRuleSetCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteReceiptRuleSetRequest;
            output: {};
        };
        sdk: {
            input: DeleteReceiptRuleSetCommandInput;
            output: DeleteReceiptRuleSetCommandOutput;
        };
    };
}
