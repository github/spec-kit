import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetSendStatisticsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetSendStatisticsCommand}.
 */
export interface GetSendStatisticsCommandInput {
}
/**
 * @public
 *
 * The output of {@link GetSendStatisticsCommand}.
 */
export interface GetSendStatisticsCommandOutput extends GetSendStatisticsResponse, __MetadataBearer {
}
declare const GetSendStatisticsCommand_base: {
    new (input: GetSendStatisticsCommandInput): import("@smithy/smithy-client").CommandImpl<GetSendStatisticsCommandInput, GetSendStatisticsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [GetSendStatisticsCommandInput]): import("@smithy/smithy-client").CommandImpl<GetSendStatisticsCommandInput, GetSendStatisticsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Provides sending statistics for the current Amazon Web Services Region. The result is a list of data
 *             points, representing the last two weeks of sending activity. Each data point in the list
 *             contains statistics for a 15-minute period of time.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetSendStatisticsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetSendStatisticsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = {};
 * const command = new GetSendStatisticsCommand(input);
 * const response = await client.send(command);
 * // { // GetSendStatisticsResponse
 * //   SendDataPoints: [ // SendDataPointList
 * //     { // SendDataPoint
 * //       Timestamp: new Date("TIMESTAMP"),
 * //       DeliveryAttempts: Number("long"),
 * //       Bounces: Number("long"),
 * //       Complaints: Number("long"),
 * //       Rejects: Number("long"),
 * //     },
 * //   ],
 * // };
 *
 * ```
 *
 * @param GetSendStatisticsCommandInput - {@link GetSendStatisticsCommandInput}
 * @returns {@link GetSendStatisticsCommandOutput}
 * @see {@link GetSendStatisticsCommandInput} for command's `input` shape.
 * @see {@link GetSendStatisticsCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example GetSendStatistics
 * ```javascript
 * // The following example returns Amazon SES sending statistics:
 * const input = { /* empty *\/ };
 * const command = new GetSendStatisticsCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   SendDataPoints: [
 *     {
 *       Bounces: 0,
 *       Complaints: 0,
 *       DeliveryAttempts: 5,
 *       Rejects: 0,
 *       Timestamp: "2016-07-13T22:43:00Z"
 *     },
 *     {
 *       Bounces: 0,
 *       Complaints: 0,
 *       DeliveryAttempts: 3,
 *       Rejects: 0,
 *       Timestamp: "2016-07-13T23:13:00Z"
 *     },
 *     {
 *       Bounces: 0,
 *       Complaints: 0,
 *       DeliveryAttempts: 1,
 *       Rejects: 0,
 *       Timestamp: "2016-07-13T21:13:00Z"
 *     }
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class GetSendStatisticsCommand extends GetSendStatisticsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: {};
            output: GetSendStatisticsResponse;
        };
        sdk: {
            input: GetSendStatisticsCommandInput;
            output: GetSendStatisticsCommandOutput;
        };
    };
}
