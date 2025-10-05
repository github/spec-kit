import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListConfigurationSetsRequest, ListConfigurationSetsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListConfigurationSetsCommand}.
 */
export interface ListConfigurationSetsCommandInput extends ListConfigurationSetsRequest {
}
/**
 * @public
 *
 * The output of {@link ListConfigurationSetsCommand}.
 */
export interface ListConfigurationSetsCommandOutput extends ListConfigurationSetsResponse, __MetadataBearer {
}
declare const ListConfigurationSetsCommand_base: {
    new (input: ListConfigurationSetsCommandInput): import("@smithy/smithy-client").CommandImpl<ListConfigurationSetsCommandInput, ListConfigurationSetsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [ListConfigurationSetsCommandInput]): import("@smithy/smithy-client").CommandImpl<ListConfigurationSetsCommandInput, ListConfigurationSetsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Provides a list of the configuration sets associated with your Amazon SES account in the
 *             current Amazon Web Services Region. For information about using configuration sets, see <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Monitoring
 *                 Your Amazon SES Sending Activity</a> in the <i>Amazon SES Developer
 *                 Guide.</i>
 *          </p>
 *          <p>You can execute this operation no more than once per second. This operation returns up
 *             to 1,000 configuration sets each time it is run. If your Amazon SES account has more than
 *             1,000 configuration sets, this operation also returns <code>NextToken</code>. You can
 *             then execute the <code>ListConfigurationSets</code> operation again, passing the
 *                 <code>NextToken</code> parameter and the value of the NextToken element to retrieve
 *             additional results.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, ListConfigurationSetsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ListConfigurationSetsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // ListConfigurationSetsRequest
 *   NextToken: "STRING_VALUE",
 *   MaxItems: Number("int"),
 * };
 * const command = new ListConfigurationSetsCommand(input);
 * const response = await client.send(command);
 * // { // ListConfigurationSetsResponse
 * //   ConfigurationSets: [ // ConfigurationSets
 * //     { // ConfigurationSet
 * //       Name: "STRING_VALUE", // required
 * //     },
 * //   ],
 * //   NextToken: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ListConfigurationSetsCommandInput - {@link ListConfigurationSetsCommandInput}
 * @returns {@link ListConfigurationSetsCommandOutput}
 * @see {@link ListConfigurationSetsCommandInput} for command's `input` shape.
 * @see {@link ListConfigurationSetsCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class ListConfigurationSetsCommand extends ListConfigurationSetsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: ListConfigurationSetsRequest;
            output: ListConfigurationSetsResponse;
        };
        sdk: {
            input: ListConfigurationSetsCommandInput;
            output: ListConfigurationSetsCommandOutput;
        };
    };
}
