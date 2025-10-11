import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { CreateReceiptFilterRequest, CreateReceiptFilterResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateReceiptFilterCommand}.
 */
export interface CreateReceiptFilterCommandInput extends CreateReceiptFilterRequest {
}
/**
 * @public
 *
 * The output of {@link CreateReceiptFilterCommand}.
 */
export interface CreateReceiptFilterCommandOutput extends CreateReceiptFilterResponse, __MetadataBearer {
}
declare const CreateReceiptFilterCommand_base: {
    new (input: CreateReceiptFilterCommandInput): import("@smithy/smithy-client").CommandImpl<CreateReceiptFilterCommandInput, CreateReceiptFilterCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: CreateReceiptFilterCommandInput): import("@smithy/smithy-client").CommandImpl<CreateReceiptFilterCommandInput, CreateReceiptFilterCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Creates a new IP address filter.</p>
 *          <p>For information about setting up IP address filters, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-ip-filtering-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, CreateReceiptFilterCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, CreateReceiptFilterCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // CreateReceiptFilterRequest
 *   Filter: { // ReceiptFilter
 *     Name: "STRING_VALUE", // required
 *     IpFilter: { // ReceiptIpFilter
 *       Policy: "Block" || "Allow", // required
 *       Cidr: "STRING_VALUE", // required
 *     },
 *   },
 * };
 * const command = new CreateReceiptFilterCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param CreateReceiptFilterCommandInput - {@link CreateReceiptFilterCommandInput}
 * @returns {@link CreateReceiptFilterCommandOutput}
 * @see {@link CreateReceiptFilterCommandInput} for command's `input` shape.
 * @see {@link CreateReceiptFilterCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link AlreadyExistsException} (client fault)
 *  <p>Indicates that a resource could not be created because of a naming conflict.</p>
 *
 * @throws {@link LimitExceededException} (client fault)
 *  <p>Indicates that a resource could not be created because of service limits. For a list
 *             of Amazon SES limits, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/limits.html">Amazon SES Developer
 *             Guide</a>.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example CreateReceiptFilter
 * ```javascript
 * // The following example creates a new IP address filter:
 * const input = {
 *   Filter: {
 *     IpFilter: {
 *       Cidr: "1.2.3.4/24",
 *       Policy: "Allow"
 *     },
 *     Name: "MyFilter"
 *   }
 * };
 * const command = new CreateReceiptFilterCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class CreateReceiptFilterCommand extends CreateReceiptFilterCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: CreateReceiptFilterRequest;
            output: {};
        };
        sdk: {
            input: CreateReceiptFilterCommandInput;
            output: CreateReceiptFilterCommandOutput;
        };
    };
}
