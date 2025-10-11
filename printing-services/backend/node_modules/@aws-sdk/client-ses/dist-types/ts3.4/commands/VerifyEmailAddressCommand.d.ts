import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { VerifyEmailAddressRequest } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface VerifyEmailAddressCommandInput
  extends VerifyEmailAddressRequest {}
export interface VerifyEmailAddressCommandOutput extends __MetadataBearer {}
declare const VerifyEmailAddressCommand_base: {
  new (
    input: VerifyEmailAddressCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyEmailAddressCommandInput,
    VerifyEmailAddressCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: VerifyEmailAddressCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyEmailAddressCommandInput,
    VerifyEmailAddressCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class VerifyEmailAddressCommand extends VerifyEmailAddressCommand_base {
  protected static __types: {
    api: {
      input: VerifyEmailAddressRequest;
      output: {};
    };
    sdk: {
      input: VerifyEmailAddressCommandInput;
      output: VerifyEmailAddressCommandOutput;
    };
  };
}
