import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ListReceiptRuleSetsRequest,
  ListReceiptRuleSetsResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ListReceiptRuleSetsCommandInput
  extends ListReceiptRuleSetsRequest {}
export interface ListReceiptRuleSetsCommandOutput
  extends ListReceiptRuleSetsResponse,
    __MetadataBearer {}
declare const ListReceiptRuleSetsCommand_base: {
  new (
    input: ListReceiptRuleSetsCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListReceiptRuleSetsCommandInput,
    ListReceiptRuleSetsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListReceiptRuleSetsCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListReceiptRuleSetsCommandInput,
    ListReceiptRuleSetsCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListReceiptRuleSetsCommand extends ListReceiptRuleSetsCommand_base {
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
