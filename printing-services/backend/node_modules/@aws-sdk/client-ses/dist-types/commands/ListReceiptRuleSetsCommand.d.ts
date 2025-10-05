import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListReceiptRuleSetsRequest, ListReceiptRuleSetsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListReceiptRuleSetsCommand}.
 */
export interface ListReceiptRuleSetsCommandInput extends ListReceiptRuleSetsRequest {
}
/**
 * @public
 *
 * The output of {@link ListReceiptRuleSetsCommand}.
 */
export interface ListReceiptRuleSetsCommandOutput extends ListReceiptRuleSetsResponse, __MetadataBearer {
}
declare const ListReceiptRuleSetsCommand_base: {
    new (input: ListReceiptRuleSetsCommandInput): import("@smithy/smithy-client").CommandImpl<ListReceiptRuleSetsCommandInput, ListReceiptRuleSetsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [ListReceiptRuleSetsCommandInput]): import("@smithy/smithy-client").CommandImpl<ListReceiptRuleSetsCommandInput, ListReceiptRuleSetsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Lists the receipt rule sets that exist under your Amazon Web Services account in the current
 *             Amazon Web Services Region. If there are additional receipt rule sets to be retrieved, you receive a
 *                 <code>NextToken</code> that you can provide to the next call to
 *                 <code>ListReceiptRuleSets</code> to retrieve the additional entries.</p>
 *          <p>For information about managing receipt rule sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/receiving-email-receipt-rules-console-walkthrough.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, ListReceiptRuleSetsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ListReceiptRuleSetsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // ListReceiptRuleSetsRequest
 *   NextToken: "STRING_VALUE",
 * };
 * const command = new ListReceiptRuleSetsCommand(input);
 * const response = await client.send(command);
 * // { // ListReceiptRuleSetsResponse
 * //   RuleSets: [ // ReceiptRuleSetsLists
 * //     { // ReceiptRuleSetMetadata
 * //       Name: "STRING_VALUE",
 * //       CreatedTimestamp: new Date("TIMESTAMP"),
 * //     },
 * //   ],
 * //   NextToken: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ListReceiptRuleSetsCommandInput - {@link ListReceiptRuleSetsCommandInput}
 * @returns {@link ListReceiptRuleSetsCommandOutput}
 * @see {@link ListReceiptRuleSetsCommandInput} for command's `input` shape.
 * @see {@link ListReceiptRuleSetsCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example ListReceiptRuleSets
 * ```javascript
 * // The following example lists the receipt rule sets that exist under an AWS account:
 * const input = {
 *   NextToken: ""
 * };
 * const command = new ListReceiptRuleSetsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   NextToken: "",
 *   RuleSets: [
 *     {
 *       CreatedTimestamp: "2016-07-15T16:25:59.607Z",
 *       Name: "MyRuleSet"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class ListReceiptRuleSetsCommand extends ListReceiptRuleSetsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: ListReceiptRuleSetsRequest;
            output: ListReceiptRuleSetsResponse;
        };
        sdk: {
            input: ListReceiptRuleSetsCommandInput;
            output: ListReceiptRuleSetsCommandOutput;
        };
    };
}
