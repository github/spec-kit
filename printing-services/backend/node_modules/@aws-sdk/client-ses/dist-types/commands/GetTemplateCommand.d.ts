import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetTemplateRequest, GetTemplateResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetTemplateCommand}.
 */
export interface GetTemplateCommandInput extends GetTemplateRequest {
}
/**
 * @public
 *
 * The output of {@link GetTemplateCommand}.
 */
export interface GetTemplateCommandOutput extends GetTemplateResponse, __MetadataBearer {
}
declare const GetTemplateCommand_base: {
    new (input: GetTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<GetTemplateCommandInput, GetTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: GetTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<GetTemplateCommandInput, GetTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Displays the template object (which includes the Subject line, HTML part and text
 *             part) for the template you specify.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetTemplateCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetTemplateCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // GetTemplateRequest
 *   TemplateName: "STRING_VALUE", // required
 * };
 * const command = new GetTemplateCommand(input);
 * const response = await client.send(command);
 * // { // GetTemplateResponse
 * //   Template: { // Template
 * //     TemplateName: "STRING_VALUE", // required
 * //     SubjectPart: "STRING_VALUE",
 * //     TextPart: "STRING_VALUE",
 * //     HtmlPart: "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param GetTemplateCommandInput - {@link GetTemplateCommandInput}
 * @returns {@link GetTemplateCommandOutput}
 * @see {@link GetTemplateCommandInput} for command's `input` shape.
 * @see {@link GetTemplateCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link TemplateDoesNotExistException} (client fault)
 *  <p>Indicates that the Template object you specified does not exist in your Amazon SES
 *             account.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class GetTemplateCommand extends GetTemplateCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: GetTemplateRequest;
            output: GetTemplateResponse;
        };
        sdk: {
            input: GetTemplateCommandInput;
            output: GetTemplateCommandOutput;
        };
    };
}
