import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  SetIdentityDkimEnabledRequest,
  SetIdentityDkimEnabledResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface SetIdentityDkimEnabledCommandInput
  extends SetIdentityDkimEnabledRequest {}
export interface SetIdentityDkimEnabledCommandOutput
  extends SetIdentityDkimEnabledResponse,
    __MetadataBearer {}
declare const SetIdentityDkimEnabledCommand_base: {
  new (
    input: SetIdentityDkimEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityDkimEnabledCommandInput,
    SetIdentityDkimEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: SetIdentityDkimEnabledCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    SetIdentityDkimEnabledCommandInput,
    SetIdentityDkimEnabledCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class SetIdentityDkimEnabledCommand extends SetIdentityDkimEnabledCommand_base {
  protected static __types: {
    api: {
      input: SetIdentityDkimEnabledRequest;
      output: {};
    };
    sdk: {
      input: SetIdentityDkimEnabledCommandInput;
      output: SetIdentityDkimEnabledCommandOutput;
    };
  };
}
