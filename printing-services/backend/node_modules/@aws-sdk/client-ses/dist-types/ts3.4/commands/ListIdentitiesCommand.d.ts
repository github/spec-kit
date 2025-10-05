import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  ListIdentitiesRequest,
  ListIdentitiesResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ListIdentitiesCommandInput extends ListIdentitiesRequest {}
export interface ListIdentitiesCommandOutput
  extends ListIdentitiesResponse,
    __MetadataBearer {}
declare const ListIdentitiesCommand_base: {
  new (
    input: ListIdentitiesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListIdentitiesCommandInput,
    ListIdentitiesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListIdentitiesCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListIdentitiesCommandInput,
    ListIdentitiesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListIdentitiesCommand extends ListIdentitiesCommand_base {
  protected static __types: {
    api: {
      input: ListIdentitiesRequest;
      output: ListIdentitiesResponse;
    };
    sdk: {
      input: ListIdentitiesCommandInput;
      output: ListIdentitiesCommandOutput;
    };
  };
}
