"""Exploratory deterministic source-only observer: generic AnimeSeg clothes -> unsupervised color/shoulder clusters.
No human label or user polygon enters predict_outerwear_shadow(). Research only.
"""
import cv2,numpy as np
SEED=20261016

def predict_outerwear_shadow(rgba:np.ndarray,classids:np.ndarray):
    if rgba.dtype!=np.uint8 or rgba.ndim!=3 or rgba.shape[2]!=4 or classids.shape!=rgba.shape[:2]:raise ValueError('bad source/observer dimensions')
    alpha=rgba[:,:,3]>0
    clothes=(classids==10)&alpha
    if clothes.sum()<1000:raise ValueError('too sparse to infer')
    lab=cv2.cvtColor(rgba[:,:,:3],cv2.COLOR_RGB2LAB)
    yy,xx=np.where(alpha)
    y0,y1=yy.min(),yy.max();x0,x1=xx.min(),xx.max()
    height=max(1,y1-y0);width=max(1,x1-x0)
    face=np.where((classids==2)&alpha)
    neckline=face[0].max()+height*.035 if len(face[0])>200 else y0+height*.26
    ygrid,xgrid=np.indices(alpha.shape)
    rx=(xgrid-x0)/width
    # Both shoulders, on upper chest below face. No manual mask or human coordinates.
    shoulder=(ygrid>neckline)&(ygrid<neckline+height*.17)&(((rx>.15)&(rx<.40))|((rx>.60)&(rx<.85)))&clothes
    if shoulder.sum()<80:raise ValueError('not enough model clothing around shoulders')
    pixels=lab[clothes].astype(np.float32)
    rng=np.random.default_rng(SEED)
    sample=pixels[rng.choice(len(pixels),min(30000,len(pixels)),replace=False)]
    cv2.setRNGSeed(SEED % 2147483647)
    _,_,centroids=cv2.kmeans(sample,8,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,20,.4),2,cv2.KMEANS_PP_CENTERS)
    # Classify all generic-clothes pixels by unsupervised centroids.
    selected=np.zeros(alpha.shape,np.uint8);positions=np.flatnonzero(clothes.ravel())
    ids=np.empty(len(positions),np.uint8)
    for start in range(0,len(positions),20000):
        chunk=pixels[start:start+20000]
        ids[start:start+20000]=np.argmin(((chunk[:,None,:]-centroids[None,:,:])**2).sum(axis=2),axis=1)
    cluster_map=np.full(alpha.shape,255,np.uint8);cluster_map.ravel()[positions]=ids
    counts=np.bincount(ids,minlength=8)
    scounts=np.bincount(cluster_map[shoulder],minlength=256)[:8]
    fractions=scounts/max(1,int(shoulder.sum()))
    # seed coverage and enrichment: keep up to 3 large shoulder clusters
    enrich=fractions/np.maximum(counts/len(ids),1e-6)
    valid=np.where((fractions>=.065)&(enrich>=.65))[0]
    chosen=valid[np.argsort(-fractions[valid])][:3]
    pred=clothes & np.isin(cluster_map,chosen)
    # No interplation, no growth, source alpha strict
    return pred,{'selected_clusters':list(map(int,chosen)),'shoulder_pixel_count':int(shoulder.sum()),'source_pixels_generated':0,'generic_clothes_px':int(clothes.sum()),'pred_pixels':int(pred.sum())}
