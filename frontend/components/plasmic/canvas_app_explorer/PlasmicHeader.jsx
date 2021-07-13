// @ts-nocheck
/* eslint-disable */
/* tslint:disable */
/* prettier-ignore-start */
/** @jsxRuntime classic */
/** @jsx createPlasmicElementProxy */
/** @jsxFrag React.Fragment */
// This class is auto-generated by Plasmic; please do not edit!
// Plasmic Project: mXv5TZ5SUPGRneH9RoMn6q
// Component: rgvwcoUrD14Pp
import * as React from "react";
import * as p from "@plasmicapp/react-web";
import {
  hasVariant,
  classNames,
  createPlasmicElementProxy,
  deriveRenderOpts,
  ensureGlobalVariants
} from "@plasmicapp/react-web";
import MenuButton from "../../MenuButton"; // plasmic-import: fd0a48CHFpLDW/component
import IconLink from "../../IconLink"; // plasmic-import: sBgr46KDuJYZz/component
import LinkButton from "../../LinkButton"; // plasmic-import: tr5phcLQqCoEx/component
import { useScreenVariants } from "./PlasmicGlobalVariant__Screen"; // plasmic-import: thj0p9NXEH81i/globalVariant
import "@plasmicapp/react-web/lib/plasmic.css";
import "../plasmic__default_style.css"; // plasmic-import: global/defaultcss
import "./plasmic_canvas_app_explorer.css"; // plasmic-import: mXv5TZ5SUPGRneH9RoMn6q/projectcss
import "./PlasmicHeader.css"; // plasmic-import: rgvwcoUrD14Pp/css
import SearchIcon from "./icons/PlasmicIcon__Search"; // plasmic-import: XYsIQokGkGcBz/icon
import CogIcon from "./icons/PlasmicIcon__Cog"; // plasmic-import: jxNUPxdPJcbB1/icon

export const PlasmicHeader__VariantProps = new Array(
  "expanded",
  "withSearchBar",
  "noSearchBarOrSettings"
);

export const PlasmicHeader__ArgProps = new Array();

function PlasmicHeader__RenderFunc(props) {
  const { variants, args, overrides, forNode, dataFetches } = props;
  const globalVariants = ensureGlobalVariants({
    screen: useScreenVariants()
  });

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
        "Header__root__r4I1P",
        {
          Header__root__expanded__r4I1Pvp9H7: hasVariant(
            variants,
            "expanded",
            "expanded"
          )
        }
      )}
    >
      <p.Stack
        as={"div"}
        hasGap={true}
        className={classNames(
          "plasmic_default__all",
          "plasmic_default__div",
          "Header__box__ikq92",
          {
            Header__box__noSearchBarOrSettings__ikq92I2VQm: hasVariant(
              variants,
              "noSearchBarOrSettings",
              "noSearchBarOrSettings"
            ),

            Header__box__withSearchBar__ikq928Xp20: hasVariant(
              variants,
              "withSearchBar",
              "withSearchBar"
            )
          }
        )}
      >
        {(hasVariant(globalVariants, "screen", "mobile") ? true : false) ? (
          <MenuButton
            data-plasmic-name={"menuButton"}
            data-plasmic-override={overrides.menuButton}
            className={classNames(
              "__wab_instance",
              "Header__menuButton__bmiow",
              {
                Header__menuButton__expanded__bmiowVp9H7: hasVariant(
                  variants,
                  "expanded",
                  "expanded"
                )
              }
            )}
            expanded={
              hasVariant(variants, "expanded", "expanded") &&
              hasVariant(globalVariants, "screen", "mobile")
                ? "expanded"
                : undefined
            }
          />
        ) : null}

        <div
          className={classNames(
            "plasmic_default__all",
            "plasmic_default__div",
            "__wab_text",
            "Header__box__keObZ"
          )}
        >
          {"Canvas App Explorer"}
        </div>

        <p.Stack
          as={"div"}
          hasGap={true}
          className={classNames(
            "plasmic_default__all",
            "plasmic_default__div",
            "Header__box__zcEqf"
          )}
        >
          <IconLink
            className={classNames("__wab_instance", "Header__iconLink__rda3A", {
              Header__iconLink__noSearchBarOrSettings__rda3Ai2VQm: hasVariant(
                variants,
                "noSearchBarOrSettings",
                "noSearchBarOrSettings"
              )
            })}
            icon={
              (
                hasVariant(
                  variants,
                  "noSearchBarOrSettings",
                  "noSearchBarOrSettings"
                )
                  ? false
                  : true
              ) ? (
                <SearchIcon
                  className={classNames(
                    "plasmic_default__all",
                    "plasmic_default__svg",
                    "Header__svg___7Ic5E",
                    {
                      Header__svg__noSearchBarOrSettings___7Ic5Ei2VQm:
                        hasVariant(
                          variants,
                          "noSearchBarOrSettings",
                          "noSearchBarOrSettings"
                        )
                    }
                  )}
                  role={"img"}
                />
              ) : null
            }
          />

          {(
            hasVariant(variants, "withSearchBar", "withSearchBar")
              ? true
              : false
          ) ? (
            <input
              className={classNames(
                "plasmic_default__all",
                "plasmic_default__input",
                "Header__textbox___8JssE",
                {
                  Header__textbox__withSearchBar___8JssE8Xp20: hasVariant(
                    variants,
                    "withSearchBar",
                    "withSearchBar"
                  )
                }
              )}
              placeholder={
                hasVariant(variants, "withSearchBar", "withSearchBar")
                  ? "filter by keyword"
                  : "Some placeholder"
              }
              size={1}
              type={"text"}
              value={
                hasVariant(variants, "withSearchBar", "withSearchBar")
                  ? ""
                  : "Some value"
              }
            />
          ) : null}
          {(
            hasVariant(
              variants,
              "noSearchBarOrSettings",
              "noSearchBarOrSettings"
            )
              ? false
              : true
          ) ? (
            <IconLink
              className={classNames(
                "__wab_instance",
                "Header__iconLink__pu1Ei",
                {
                  Header__iconLink__noSearchBarOrSettings__pu1Eii2VQm:
                    hasVariant(
                      variants,
                      "noSearchBarOrSettings",
                      "noSearchBarOrSettings"
                    )
                }
              )}
              icon={
                <CogIcon
                  className={classNames(
                    "plasmic_default__all",
                    "plasmic_default__svg",
                    "Header__svg__agh0S"
                  )}
                  role={"img"}
                />
              }
            />
          ) : null}
        </p.Stack>

        {false ? (
          <input
            className={classNames(
              "plasmic_default__all",
              "plasmic_default__input",
              "Header__textbox__cDxmy"
            )}
            placeholder={"Some placeholder"}
            size={1}
            type={"text"}
            value={"Some value"}
          />
        ) : null}
        {false ? (
          <input
            className={classNames(
              "plasmic_default__all",
              "plasmic_default__input",
              "Header__textbox__mlQAu"
            )}
            placeholder={"Some placeholder"}
            size={1}
            type={"text"}
            value={"Some value"}
          />
        ) : null}
      </p.Stack>

      {(
        hasVariant(variants, "expanded", "expanded") &&
        hasVariant(globalVariants, "screen", "mobile")
          ? true
          : false
      ) ? (
        <div
          className={classNames(
            "plasmic_default__all",
            "plasmic_default__div",
            "Header__box__qIiNj",
            {
              Header__box__expanded__qIiNjVp9H7: hasVariant(
                variants,
                "expanded",
                "expanded"
              )
            }
          )}
        >
          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__bhzkI"
            )}
            text={"Home"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__xdYja"
            )}
            text={"New Arrival"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__nKvUv"
            )}
            text={"Features"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__hk6Zt"
            )}
            text={"Blog"}
            type={"blankGray"}
          />

          <LinkButton
            className={classNames(
              "__wab_instance",
              "Header__linkButton__wWLqi"
            )}
            text={"Contact"}
            type={"blankGray"}
          />
        </div>
      ) : null}
    </div>
  );
}

const PlasmicDescendants = {
  root: ["root", "menuButton"],
  menuButton: ["menuButton"]
};

function makeNodeComponent(nodeName) {
  const func = function (props) {
    const { variants, args, overrides } = deriveRenderOpts(props, {
      name: nodeName,
      descendantNames: [...PlasmicDescendants[nodeName]],
      internalArgPropNames: PlasmicHeader__ArgProps,
      internalVariantPropNames: PlasmicHeader__VariantProps
    });

    const { dataFetches } = props;
    return PlasmicHeader__RenderFunc({
      variants,
      args,
      overrides,
      dataFetches,
      forNode: nodeName
    });
  };
  if (nodeName === "root") {
    func.displayName = "PlasmicHeader";
  } else {
    func.displayName = `PlasmicHeader.${nodeName}`;
  }
  return func;
}

export const PlasmicHeader = Object.assign(
  // Top-level PlasmicHeader renders the root element
  makeNodeComponent("root"),
  {
    // Helper components rendering sub-elements
    menuButton: makeNodeComponent("menuButton"),
    // Metadata about props expected for PlasmicHeader
    internalVariantProps: PlasmicHeader__VariantProps,
    internalArgProps: PlasmicHeader__ArgProps
  }
);

export default PlasmicHeader;
/* prettier-ignore-end */
