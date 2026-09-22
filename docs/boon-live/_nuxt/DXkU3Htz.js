import{i as r,l as t,g as a,b as n}from"./Cs1zKDta.js";const e=`
_key,
_type,
text,
showAsHoverItem,
showAsHoverItem == true => {
   "hoverImage": image {
      ${r}
   }
},
link != null => {
   ${t}
},
`,o=`
_type,
_key,
label,

'hasChildren': count(navItems) > 0,
'children': navItems[] {
   _type == 'navItem' => {
      ${e}
   },
   _type == 'navSubGroup' => {
      _type,
      _key,
      label,
      'children': navItems[] {
         ${e}
      }
   },
}`,v=a`
*[_type == 'header' && _id == 'header'][0] {
   _type,
   _rev,
   _id,
   navItems[] {
      _type == 'navItem' => {
         ${e}
      },
      _type == 'navGroup' => {
         ${o}
      },
   },
   ctaItems[] {
      ${e}
   },
   "alertBanner": *[_type == 'alertBanner' && _id == 'alertBanner' && @.active == true][0] {
      _type,
      _id,
      _rev,
      active,
      text,
      ${t}
   }
}`,y=a`*[_type == 'footer' && _id == 'footer'][0] {  
   _type,
   _id,
   _rev,
   primaryNav[] {
      _type == 'navItem' => {
         ${e}
      }
   },
   secondaryNav[] {
      _type == 'navItem' => {
         ${e}
      }
   },
   footerCta{
      ${n}
   }
}`;export{y as F,v as H};
