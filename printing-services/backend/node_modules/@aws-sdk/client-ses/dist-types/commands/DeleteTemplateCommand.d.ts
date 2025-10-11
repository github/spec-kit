import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteTemplateRequest, DeleteTemplateResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteTemplateCommand}.
 */
export interface DeleteTemplateCommandInput extends DeleteTemplateRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteTemplateCommand}.
 */
export interface DeleteTemplateCommandOutput extends DeleteTemplateResponse, __MetadataBearer {
}
declare const DeleteTemplateCommand_base: {
    new (input: DeleteTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteTemplateCommandInput, DeleteTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteTemplateCommandInput, DeleteTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes an email template.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteTemplateCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteTemplateCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteTemplateRequest
 *   TemplateName: "STRING_VALUE", // required
 * };
 * const command = new DeleteTemplateCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteTemplateCommandInput - {@link DeleteTemplateCommandInput}
 * @returns {@link DeleteTemplateCommandOutput}
 * @see {@link DeleteTemplateCommandInput} for command's `input` shape.
 * @see {@link DeleteTemplateCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class DeleteTemplateCommand extends DeleteTemplateCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteTemplateRequest;
            output: {};
        };
        sdk: {
            input: DeleteTemplateCommandInput;
            output: DeleteTemplateCommandOutput;
        };
    };
}
