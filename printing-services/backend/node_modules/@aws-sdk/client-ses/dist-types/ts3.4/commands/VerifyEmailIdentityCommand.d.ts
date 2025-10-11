import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  VerifyEmailIdentityRequest,
  VerifyEmailIdentityResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface VerifyEmailIdentityCommandInput
  extends VerifyEmailIdentityRequest {}
export interface VerifyEmailIdentityCommandOutput
  extends VerifyEmailIdentityResponse,
    __MetadataBearer {}
declare const VerifyEmailIdentityCommand_base: {
  new (
    input: VerifyEmailIdentityCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyEmailIdentityCommandInput,
    VerifyEmailIdentityCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: VerifyEmailIdentityCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    VerifyEmailIdentityCommandInput,
    VerifyEmailIdentityCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class VerifyEmailIdentityCommand extends VerifyEmailIdentityCommand_base {
  protected static __types: {
    api: {
      input: VerifyEmailIdentityRequest;
      output: {};
    };
    sdk: {
      input: VerifyEmailIdentityCommandInput;
      output: VerifyEmailIdentityCommandOutput;
    };
  };
}
