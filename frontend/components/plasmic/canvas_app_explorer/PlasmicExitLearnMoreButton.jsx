// @ts-nocheck
/* eslint-disable */
/* tslint:disable */
/* prettier-ignore-start */
/** @jsxRuntime classic */
/** @jsx createPlasmicElementProxy */
/** @jsxFrag React.Fragment */
// This class is auto-generated by Plasmic; please do not edit!
// Plasmic Project: mXv5TZ5SUPGRneH9RoMn6q
// Component: 6fH9bcqROh
import * as React from "react";
import {
  classNames,
  createPlasmicElementProxy,
  deriveRenderOpts
} from "@plasmicapp/react-web";
import "@plasmicapp/react-web/lib/plasmic.css";
import "../plasmic__default_style.css"; // plasmic-import: global/defaultcss
import "./plasmic_canvas_app_explorer.css"; // plasmic-import: mXv5TZ5SUPGRneH9RoMn6q/projectcss
import "./PlasmicExitLearnMoreButton.css"; // plasmic-import: 6fH9bcqROh/css

export const PlasmicExitLearnMoreButton__VariantProps = new Array();

export const PlasmicExitLearnMoreButton__ArgProps = new Array();

function PlasmicExitLearnMoreButton__RenderFunc(props) {
  const { variants, args, overrides, forNode, dataFetches } = props;
  return (
    <div
      data-plasmic-name={"root"}
      data-plasmic-override={overrides.root}
      data-plasmic-root={true}
      data-plasmic-for-node={forNode}
      className={classNames(
        "plasmic_default__all",
        "plasmic_default__div",
        "root_reset_mXv5TZ5SUPGRneH9RoMn6q",
        "ExitLearnMoreButton__root__nnKr"
      )}
    >
      <div
        data-plasmic-name={"freeBox"}
        data-plasmic-override={overrides.freeBox}
        className={classNames(
          "plasmic_default__all",
          "plasmic_default__div",
          "__wab_text",
          "ExitLearnMoreButton__freeBox__juM6I"
        )}
      >
        {" X "}
      </div>
    </div>
  );
}

const PlasmicDescendants = {
  root: ["root", "freeBox"],
  freeBox: ["freeBox"]
};

function makeNodeComponent(nodeName) {
  const func = function (props) {
    const { variants, args, overrides } = deriveRenderOpts(props, {
      name: nodeName,
      descendantNames: [...PlasmicDescendants[nodeName]],
      internalArgPropNames: PlasmicExitLearnMoreButton__ArgProps,
      internalVariantPropNames: PlasmicExitLearnMoreButton__VariantProps
    });

    const { dataFetches } = props;
    return PlasmicExitLearnMoreButton__RenderFunc({
      variants,
      args,
      overrides,
      dataFetches,
      forNode: nodeName
    });
  };
  if (nodeName === "root") {
    func.displayName = "PlasmicExitLearnMoreButton";
  } else {
    func.displayName = `PlasmicExitLearnMoreButton.${nodeName}`;
  }
  return func;
}

export const PlasmicExitLearnMoreButton = Object.assign(
  // Top-level PlasmicExitLearnMoreButton renders the root element
  makeNodeComponent("root"),
  {
    // Helper components rendering sub-elements
    freeBox: makeNodeComponent("freeBox"),
    // Metadata about props expected for PlasmicExitLearnMoreButton
    internalVariantProps: PlasmicExitLearnMoreButton__VariantProps,
    internalArgProps: PlasmicExitLearnMoreButton__ArgProps
  }
);

export default PlasmicExitLearnMoreButton;
/* prettier-ignore-end */
