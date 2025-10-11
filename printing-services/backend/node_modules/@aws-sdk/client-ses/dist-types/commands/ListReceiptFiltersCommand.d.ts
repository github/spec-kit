import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListReceiptFiltersRequest, ListReceiptFiltersResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListReceiptFiltersCommand}.
 */
export interface ListReceiptFiltersCommandInput extends ListReceiptFiltersRequest {
}
/**
 * @public
 *
 * The output of {@link ListReceiptFiltersCommand}.
 */
export interface ListReceiptFiltersCommandOutput extends ListReceiptFiltersResponse, __MetadataBearer {
}
declare const ListReceiptFiltersCommand_base: {
    new (input: ListReceiptFiltersCommandInput): import("@smithy/smithy-client").CommandImpl<ListReceiptFiltersCommandInput, ListReceiptFiltersCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [ListReceiptFiltersCommandInput]): import("@smithy/smithy-client").CommandImpl<ListReceiptFiltersCommandInput, ListReceiptFiltersCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Lists the IP address filters associated with your Amazon Web Services account in the current
 *             Amazon Web Services Region.</p>
 *          <p>For information about managing IP address filters, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-ip-filtering-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, ListReceiptFiltersCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ListReceiptFiltersCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = {};
 * const command = new ListReceiptFiltersCommand(input);
 * const response = await client.send(command);
 * // { // ListReceiptFiltersResponse
 * //   Filters: [ // ReceiptFilterList
 * //     { // ReceiptFilter
 * //       Name: "STRING_VALUE", // required
 * //       IpFilter: { // ReceiptIpFilter
 * //         Policy: "Block" || "Allow", // required
 * //         Cidr: "STRING_VALUE", // required
 * //       },
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListReceiptFiltersCommandInput - {@link ListReceiptFiltersCommandInput}
 * @returns {@link ListReceiptFiltersCommandOutput}
 * @see {@link ListReceiptFiltersCommandInput} for command's `input` shape.
 * @see {@link ListReceiptFiltersCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example ListReceiptFilters
 * ```javascript
 * // The following example lists the IP address filters that are associated with an AWS account:
 * const input = { /* empty *\/ };
 * const command = new ListReceiptFiltersCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   Filters: [
 *     {
 *       IpFilter: {
 *         Cidr: "1.2.3.4/24",
 *         Policy: "Block"
 *       },
 *       Name: "MyFilter"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class ListReceiptFiltersCommand extends ListReceiptFiltersCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: {};
            output: ListReceiptFiltersResponse;
        };
        sdk: {
            input: ListReceiptFiltersCommandInput;
            output: ListReceiptFiltersCommandOutput;
        };
    };
}
