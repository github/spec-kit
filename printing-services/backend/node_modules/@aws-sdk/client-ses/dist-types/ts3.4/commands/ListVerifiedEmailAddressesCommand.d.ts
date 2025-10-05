import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListVerifiedEmailAddressesResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface ListVerifiedEmailAddressesCommandInput {}
export interface ListVerifiedEmailAddressesCommandOutput
  extends ListVerifiedEmailAddressesResponse,
    __MetadataBearer {}
declare const ListVerifiedEmailAddressesCommand_base: {
  new (
    input: ListVerifiedEmailAddressesCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    ListVerifiedEmailAddressesCommandInput,
    ListVerifiedEmailAddressesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    ...[input]: [] | [ListVerifiedEmailAddressesCommandInput]
  ): import("@smithy/smithy-client").CommandImpl<
    ListVerifiedEmailAddressesCommandInput,
    ListVerifiedEmailAddressesCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class ListVerifiedEmailAddressesCommand extends ListVerifiedEmailAddressesCommand_base {
  protected static __types: {
    api: {
      input: {};
      output: ListVerifiedEmailAddressesResponse;
    };
    sdk: {
      input: ListVerifiedEmailAddressesCommandInput;
      output: ListVerifiedEmailAddressesCommandOutput;
    };
  };
}
