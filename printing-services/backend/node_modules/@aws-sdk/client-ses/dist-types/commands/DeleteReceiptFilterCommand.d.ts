import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteReceiptFilterRequest, DeleteReceiptFilterResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteReceiptFilterCommand}.
 */
export interface DeleteReceiptFilterCommandInput extends DeleteReceiptFilterRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteReceiptFilterCommand}.
 */
export interface DeleteReceiptFilterCommandOutput extends DeleteReceiptFilterResponse, __MetadataBearer {
}
declare const DeleteReceiptFilterCommand_base: {
    new (input: DeleteReceiptFilterCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteReceiptFilterCommandInput, DeleteReceiptFilterCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteReceiptFilterCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteReceiptFilterCommandInput, DeleteReceiptFilterCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes the specified IP address filter.</p>
 *          <p>For information about managing IP address filters, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-ip-filtering-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteReceiptFilterCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteReceiptFilterCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteReceiptFilterRequest
 *   FilterName: "STRING_VALUE", // required
 * };
 * const command = new DeleteReceiptFilterCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteReceiptFilterCommandInput - {@link DeleteReceiptFilterCommandInput}
 * @returns {@link DeleteReceiptFilterCommandOutput}
 * @see {@link DeleteReceiptFilterCommandInput} for command's `input` shape.
 * @see {@link DeleteReceiptFilterCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example DeleteReceiptFilter
 * ```javascript
 * // The following example deletes an IP address filter:
 * const input = {
 *   FilterName: "MyFilter"
 * };
 * const command = new DeleteReceiptFilterCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class DeleteReceiptFilterCommand extends DeleteReceiptFilterCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteReceiptFilterRequest;
            output: {};
        };
        sdk: {
            input: DeleteReceiptFilterCommandInput;
            output: DeleteReceiptFilterCommandOutput;
        };
    };
}
