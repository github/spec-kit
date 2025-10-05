import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListTemplatesRequest, ListTemplatesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListTemplatesCommand}.
 */
export interface ListTemplatesCommandInput extends ListTemplatesRequest {
}
/**
 * @public
 *
 * The output of {@link ListTemplatesCommand}.
 */
export interface ListTemplatesCommandOutput extends ListTemplatesResponse, __MetadataBearer {
}
declare const ListTemplatesCommand_base: {
    new (input: ListTemplatesCommandInput): import("@smithy/smithy-client").CommandImpl<ListTemplatesCommandInput, ListTemplatesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [ListTemplatesCommandInput]): import("@smithy/smithy-client").CommandImpl<ListTemplatesCommandInput, ListTemplatesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Lists the email templates present in your Amazon SES account in the current
 *             Amazon Web Services Region.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, ListTemplatesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ListTemplatesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // ListTemplatesRequest
 *   NextToken: "STRING_VALUE",
 *   MaxItems: Number("int"),
 * };
 * const command = new ListTemplatesCommand(input);
 * const response = await client.send(command);
 * // { // ListTemplatesResponse
 * //   TemplatesMetadata: [ // TemplateMetadataList
 * //     { // TemplateMetadata
 * //       Name: "STRING_VALUE",
 * //       CreatedTimestamp: new Date("TIMESTAMP"),
 * //     },
 * //   ],
 * //   NextToken: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ListTemplatesCommandInput - {@link ListTemplatesCommandInput}
 * @returns {@link ListTemplatesCommandOutput}
 * @see {@link ListTemplatesCommandInput} for command's `input` shape.
 * @see {@link ListTemplatesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class ListTemplatesCommand extends ListTemplatesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: ListTemplatesRequest;
            output: ListTemplatesResponse;
        };
        sdk: {
            input: ListTemplatesCommandInput;
            output: ListTemplatesCommandOutput;
        };
    };
}
