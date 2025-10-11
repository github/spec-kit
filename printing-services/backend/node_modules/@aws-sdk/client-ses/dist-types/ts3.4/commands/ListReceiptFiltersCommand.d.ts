import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ListReceiptFiltersRequest,
  ListReceiptFiltersResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ListReceiptFiltersCommandInput
  extends ListReceiptFiltersRequest {}
export interface ListReceiptFiltersCommandOutput
  extends ListReceiptFiltersResponse,
    __MetadataBearer {}
declare const ListReceiptFiltersCommand_base: {
  new (
    input: ListReceiptFiltersCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListReceiptFiltersCommandInput,
    ListReceiptFiltersCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListReceiptFiltersCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListReceiptFiltersCommandInput,
    ListReceiptFiltersCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListReceiptFiltersCommand extends ListReceiptFiltersCommand_base {
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
