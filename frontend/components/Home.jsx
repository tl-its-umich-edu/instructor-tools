// This is a skeleton starter React component generated by Plasmic.
// This file is owned by you, feel free to edit as you see fit.
import * as React from "react";
import { useState, useEffect } from "react";
import { PlasmicHome } from "./plasmic/canvas_app_explorer/PlasmicHome";
import * as p from "@plasmicapp/react-web";
import {
  classNames,
  createPlasmicElementProxy,
  deriveRenderOpts,
  ensureGlobalVariants
} from "@plasmicapp/react-web";
import Header from "./Header"; // plasmic-import: rgvwcoUrD14Pp/component
import ProductCard from "./ProductCard"; // plasmic-import: zc_-JZqmkLhAk/component
import Ratings from "./Ratings"; // plasmic-import: kZJnDl5cN7jJ7/component
import AddRemoveButton from "./AddRemoveButton"; // plasmic-import: JyIyDBiGW-/component
import LearnMoreButton from "./LearnMoreButton"; // plasmic-import: dm73fzeGC7/component
import Screenshot from "./Screenshot"; // plasmic-import: fUpKi24Qhx/component
import Footer from "./Footer"; // plasmic-import: SxuS7aSzfTV9l/component
import { useScreenVariants } from "./plasmic/canvas_app_explorer/PlasmicGlobalVariant__Screen"; // plasmic-import: thj0p9NXEH81i/globalVariant
import "@plasmicapp/react-web/lib/plasmic.css";
import "./plasmic/plasmic__default_style.css"; // plasmic-import: global/defaultcss
import "./plasmic/canvas_app_explorer/plasmic_canvas_app_explorer.css"; // plasmic-import: mXv5TZ5SUPGRneH9RoMn6q/projectcss
import "./plasmic/canvas_app_explorer/PlasmicHome.css"; // plasmic-import: 4XPgsAhljqdds/css
export const Home__VariantProps = new Array();
export const Home__ArgProps = new Array();
function Home__RenderFunc(props,ref) {  
    const [addedTools, setAddedTools] = useState([]); // each tool has one entry in array
    const [learnMoreActive, setLearnMoreActive] = useState([]); // each tool has one entry in array
    const [tools, setTools] = useState(null);

    useEffect(async () => {
        const url = "http://localhost:5000/api/lti_tools/";
        const response = await fetch(url);
        const data = await response.json();
        setTools(data)
        setAddedTools(Array(Object.keys(data).length + 2).fill(false))
        setLearnMoreActive(Array(Object.keys(data).length + 2).fill(false))
    }, []);

	const { variants, args, overrides, forNode, dataFetches } = props;
	const globalVariants = ensureGlobalVariants({
		screen: useScreenVariants()
	});
	return (
		<React.Fragment>
			<div className={"plasmic_page_wrapper"}>
				<div
					data-plasmic-name={"root"}
					data-plasmic-override={overrides.root}
					data-plasmic-root={true}
					data-plasmic-for-node={forNode}
					className={classNames(
						"plasmic_default__all",
						"plasmic_default__div",
						"root_reset_mXv5TZ5SUPGRneH9RoMn6q",
						"Home__root__rfWi8"
					)}
				>
					{false ? (
						<input
							className={classNames(
								"plasmic_default__all",
								"plasmic_default__input",
								"Home__textbox__kcHjj"
							)}
							placeholder={"Some placeholder"}
							size={1}
							type={"text"}
							value={"Some value"}
						/>
					) : null}
					<div
						data-plasmic-name={"appContainer"}
						data-plasmic-override={overrides.appContainer}
						className={classNames(
							"plasmic_default__all",
							"plasmic_default__div",
							"Home__appContainer___8LuQk"
						)}
					>
						<Header
                            data-plasmic-name={"header"}
                            data-plasmic-override={overrides.header}
                            className={classNames("__wab_instance", "Home__header__iXzGr")}
                            noSearchBarOrSettings={"noSearchBarOrSettings"}
						/>
						{false ? (
                            <input
                                className={classNames(
                                "plasmic_default__all",
                                "plasmic_default__input",
                                "Home__textbox__y0QeV"
                                )}
                                placeholder={"Some placeholder"}
                                size={1}
                                type={"text"}
                                value={"Some value"}
                            />
                        ) : null}

                        <div
                            data-plasmic-name={"caeDescriptionContainer"}
                            data-plasmic-override={overrides.caeDescriptionContainer}
                            className={classNames(
                                "plasmic_default__all",
                                "plasmic_default__div",
                                "Home__caeDescriptionContainer__d20ZQ"
                            )}
                        >
                            <div
                                className={classNames(
                                    "plasmic_default__all",
                                    "plasmic_default__div",
                                    "__wab_text",
                                    "Home__freeBox__k3LxN"
                                )}
                            >
                                {
                                    "Canvas App Explorer is a collection of resources to assist the instructor in using the best tools available for you and your students. "
                                }
                            </div>
                        </div>
                        
						<p.Stack
							as={"div"}
							data-plasmic-name={"productCardContainer"}
							data-plasmic-override={overrides.productCardContainer}
							hasGap={true}
							className={classNames(
								"plasmic_default__all",
								"plasmic_default__div",
								"Home__productCardContainer___92DMt"
							)}
						>
                        {tools === null ? (<div>Loading . . . </div>) : (
							tools.map(tool => ( 
                                <div>
                                    {learnMoreActive[tool.id] === false ?
                                        <ProductCard
                                            data-plasmic-name={tool.name+"Card"}
                                            data-plasmic-override={overrides.zoomCard}
                                            // -----------------------ADD/REMOVE BUTTON FUNCTIONALITY CODE---------------------------
                                            // addRemoveSlot={(
                                            //     <div>
                                            //         {addedTools[tool.id] === false ?  
                                            //             <AddRemoveButton
                                            //                 onClick={(e) => {
                                            //                     console.log(HELLOOO)
                                            //                     e.preventDefault(); 
                                            //                     let addedToolsCopy = [...addedTools]
                                            //                     addedToolsCopy[tool.id] = !addedToolsCopy[tool.id]
                                            //                     setAddedTools(addedToolsCopy)
                                            //                 }}
                                            //                 className={classNames(
                                            //                     "__wab_instance",
                                            //                     // "Home__addRemoveButton___3D93M" // I don't see any changes in formatting with this line
                                            //                 )}
                                            //             />
                                            //         :
                                            //             <AddRemoveButton
                                            //                 onClick={(e) => {
                                            //                     console.log(YOOOOOOOOO)
                                            //                     e.preventDefault(); 
                                            //                     let addedToolsCopy = [...addedTools]
                                            //                     addedToolsCopy[tool.id] = !addedToolsCopy[tool.id]
                                            //                     setAddedTools(addedToolsCopy)
                                            //                 }}
                                            //                 className={classNames(
                                            //                     "__wab_instance",
                                            //                     // "Home__addRemoveButton___3D93M" // I don't see any changes in formatting with this line
                                            //                 )}
                                            //                 removeToolFromSite={"removeToolFromSite"}
                                            //             />     
                                            //         } 
                                            //     </div>
                                            // )}
                                            onlyLearnMore={"onlyLearnMore"}
                                            learnMoreSlot={
                                                <LearnMoreButton
                                                    onClick={(e) => {
                                                        e.preventDefault(); 
                                                        let learnMoreActiveCopy = [...learnMoreActive]
                                                        learnMoreActiveCopy[tool.id] = !learnMoreActiveCopy[tool.id]
                                                        setLearnMoreActive(learnMoreActiveCopy)
                                                    }}
                                                    className={classNames(
                                                        "__wab_instance",
                                                        // "Home__learnMoreButton__j6ASy"// I don't see any changes in formatting with this line
                                                    )}
                                                />
                                            }

                                            className={classNames(
                                                "__wab_instance",	
                                                // "Home__zoomCard__foQyr" // I don't see any changes in formatting with this line
                                            )}
                                            description={
                                                <div
                                                  className={classNames(
                                                    "plasmic_default__all",
                                                    "plasmic_default__div",
                                                    "__wab_text",
                                                    "Home__freeBox__c1Y5M"
                                                  )}
                                                >
                                                  {tool.short_description}
                                                </div>
                                            }
                                            image={
                                                <img
                                                    alt={""}
                                                    className={classNames(
                                                        "plasmic_default__all",
                                                        "plasmic_default__img",
                                                        "Home__img__psMY" // if this line isn't here, the image won't be formatted
                                                    )}
                                                    role={"img"}
                                                    src={tool.main_image} // Image not currently in API
                                                />
                                            }
                                            logo={
                                                <img
                                                    alt={""}
                                                    className={classNames(
                                                        "plasmic_default__all",
                                                        "plasmic_default__img",
                                                        "Home__img__u0Ib1" // if this line isn't here, the images won't be formatted
                                                    )}
                                                    role={"img"}
                                                    src={tool.logo_image}
                                                />
                                            }
                                            ratings={ // Optional ratings addition, currently is not active
                                                true ? (
                                                <Ratings
                                                    className={classNames(
                                                    "__wab_instance",
                                                    "Home__ratings__iUUiJ"
                                                    )}
                                                    numReviews={"(45 Review)"}
                                                    stars={"five"}
                                                />
                                                ) : null
                                            }
                                            title={tool.name}
                                        >
                                        </ProductCard>   
                                    :
                                        <ProductCard // Other side of the Learn More If
                                            data-plasmic-name={tool.name+"Card"}
                                            data-plasmic-override={overrides.zoomCard}
                                            learnMore={"learnMore"} // if this line is commented, the card will be flipped
                                            toolLearnMore={
                                                <div
                                                  className={classNames(
                                                    "plasmic_default__all",
                                                    "plasmic_default__div",
                                                    "__wab_text",
                                                    "Home__freeBox__dHRrw"
                                                  )}
                                                >
                                                  <span>
                                                    <span style={{ fontWeight: 700 }}>{"Tool"}</span>
                                                    <React.Fragment>{"\n"}{tool.name}</React.Fragment>
                                                  </span>
                                                </div>
                                            }
                                            descriptionLearnMore={
                                                <span>
                                                  <span style={{ fontWeight: 700 }}>{"Description"}</span>
                                                  <React.Fragment>
                                                    {"\n"}    
                                                    {tool.long_description}
                                                  </React.Fragment>
                                                </span>
                                            }
                                            privacyAgreementLearnMore={
                                                <div
                                                  className={classNames(
                                                    "plasmic_default__all",
                                                    "plasmic_default__div",
                                                    "__wab_text",
                                                    "Home__freeBox__pkIjF"
                                                  )}
                                                >
                                                  <span>
                                                    <span style={{ fontWeight: 700 }}>
                                                      {"Privacy Agreement"}
                                                    </span>
                                                    <React.Fragment>
                                                      {"\n"}
                                                      {tool.privacy_agreement}
                                                      {"\n"}
                                                    </React.Fragment>
                                                  </span>
                                                </div>
                                            }
                                            placementsInCanvasLearnMore={
                                                <span>
                                                  <span style={{ fontWeight: 700 }}>
                                                    {"Placements in Canvas"}
                                                  </span>
                                                  <React.Fragment>
                                                      {"\n"}
                                                      {tool.canvas_placement_expanded.map(tool => tool.name)}</React.Fragment>
                                                </span>
                                            }
                                            supportResourcesLearnMore={
                                                <span>
                                                  <span style={{ fontWeight: 700 }}>
                                                    {"Support Resources"}
                                                  </span>
                                                  <React.Fragment>
                                                    {"\n"}
                                                    {tool.support_resources}
                                                  </React.Fragment>
                                                </span>
                                            }
                                        >
                                        </ProductCard>   
                                    }
                                </div>
                            ))
                                        
                        )}
	
						</p.Stack>
						{true ? (
							<Footer
								data-plasmic-name={"footer"}
								data-plasmic-override={overrides.footer}
								className={classNames("__wab_instance", "Home__footer__sUgvZ")}
							/>
						) : null}
					</div>
					{false ? (
						<input
							className={classNames(
								"plasmic_default__all",
								"plasmic_default__input",
								"Home__textbox__triAl"
							)}
							placeholder={"Some placeholder"}
							size={1}
							type={"text"}
							value={"Some value"}
						/>
					) : null}
				</div>
			</div>
		</React.Fragment>
	);
};    
const PlasmicDescendants = {
  root: [
    "root",
    "appContainer",
    "header",
    "caeDescriptionContainer",
    "productCardContainer",
    "zoomCard",
    "myLaCard",
    "piazzaCard",
    "panoptoCard",
    "footer"
  ],
  appContainer: [
    "appContainer",
    "header",
    "caeDescriptionContainer",
    "productCardContainer",
    "zoomCard",
    "myLaCard",
    "piazzaCard",
    "panoptoCard",
    "footer"
  ],
  header: ["header"],
  caeDescriptionContainer: ["caeDescriptionContainer"],
  productCardContainer: [
    "productCardContainer",
    "zoomCard",
    "myLaCard",
    "piazzaCard",
    "panoptoCard"
  ],
  zoomCard: ["zoomCard"],
  myLaCard: ["myLaCard"],
  piazzaCard: ["piazzaCard"],
  panoptoCard: ["panoptoCard"],
  footer: ["footer"]
};
function makeNodeComponent(nodeName) {
  const func = function (props) {
    const { variants, args, overrides } = deriveRenderOpts(props, {
      name: nodeName,
      descendantNames: [...PlasmicDescendants[nodeName]],
      internalArgPropNames: Home__ArgProps,
      internalVariantPropNames: Home__VariantProps
    });
    const { dataFetches } = props;
    return Home__RenderFunc({
      variants,
      args,
      overrides,
      dataFetches,
      forNode: nodeName
    });
  };
  if (nodeName === "root") {
    func.displayName = "Home";
  } else {
    func.displayName = `Home.${nodeName}`;
  }
  return func;
}
export const Home = Object.assign(
  // Top-level PlasmicHome renders the root element
  makeNodeComponent("root"),
  {
    // Helper components rendering sub-elements
    appContainer: makeNodeComponent("appContainer"),
    header: makeNodeComponent("header"),
    caeDescriptionContainer: makeNodeComponent("caeDescriptionContainer"),
    productCardContainer: makeNodeComponent("productCardContainer"),
    zoomCard: makeNodeComponent("zoomCard"),
    myLaCard: makeNodeComponent("myLaCard"),
    piazzaCard: makeNodeComponent("piazzaCard"),
    panoptoCard: makeNodeComponent("panoptoCard"),
    footer: makeNodeComponent("footer"),
    // Metadata about props expected for PlasmicHome
    internalVariantProps: Home__VariantProps,
    internalArgProps: Home__ArgProps
  }
);
export default Home;